from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.constants import EquipmentStatus
from backend.core.roles import UserRole
from backend.models.equipment import Equipment
from backend.models.escola import Escola
from backend.models.movement import Movement
from backend.models.saved_report import SavedReport

REPORT_TYPE_LABELS = {
    "general_summary": "Resumo geral do parque tecnologico",
    "equipments_by_school": "Equipamentos por escola",
    "equipments_by_status": "Equipamentos por status",
    "maintenance_items": "Itens em manutencao",
    "transfers_by_period": "Transferencias por periodo",
    "schools_with_most_defects": "Escolas com maior quantidade de defeitos",
    "stale_equipments": "Equipamentos sem movimentacao recente",
}


def _now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ensure_can_view_reports(current_user: dict) -> None:
    if current_user["role"] == UserRole.SUPER_ADMIN:
        return

    if current_user.get("permissions", {}).get("pode_ver_dashboard"):
        return

    raise HTTPException(status_code=403, detail="Sem permissao para visualizar relatorios")


def _can_access_saved_report(report: SavedReport, current_user: dict) -> bool:
    if current_user["role"] == UserRole.SUPER_ADMIN:
        return True

    return report.criado_por_id == current_user["id"]


def _visible_school_ids(db: Session, current_user: dict) -> set[int]:
    if current_user["role"] == UserRole.SUPER_ADMIN:
        return {school.id for school in db.query(Escola.id).all()}

    school_id = current_user.get("school_id")
    return {school_id} if school_id is not None else set()


def _visible_equipments(db: Session, current_user: dict) -> list[Equipment]:
    if current_user["role"] == UserRole.SUPER_ADMIN:
        return db.query(Equipment).all()

    school_id = current_user.get("school_id")
    if school_id is None:
        return []

    return db.query(Equipment).filter(Equipment.escola_atual_id == school_id).all()


def _filtered_visible_equipments(
    db: Session,
    current_user: dict,
    school_ids: list[int] | None = None,
    equipment_ids: list[int] | None = None,
    statuses: list[str] | None = None,
) -> list[Equipment]:
    visible = _visible_equipments(db, current_user)
    visible_school_ids = _visible_school_ids(db, current_user)
    selected_school_ids = set(school_ids or [])
    selected_equipment_ids = set(equipment_ids or [])
    selected_statuses = set(statuses or [])
    valid_statuses = {status.value for status in EquipmentStatus}

    if selected_school_ids and not selected_school_ids.issubset(visible_school_ids):
        raise HTTPException(status_code=403, detail="Sem acesso a uma das escolas selecionadas")

    if selected_statuses and not selected_statuses.issubset(valid_statuses):
        raise HTTPException(status_code=422, detail="Status de equipamento invalido")

    visible_equipment_ids = {equipment.id for equipment in visible}
    if selected_equipment_ids and not selected_equipment_ids.issubset(visible_equipment_ids):
        raise HTTPException(status_code=403, detail="Sem acesso a um dos equipamentos selecionados")

    result = []
    for equipment in visible:
        status = equipment.status.value if hasattr(equipment.status, "value") else str(equipment.status)
        if selected_school_ids and equipment.escola_atual_id not in selected_school_ids:
            continue
        if selected_equipment_ids and equipment.id not in selected_equipment_ids:
            continue
        if selected_statuses and status not in selected_statuses:
            continue
        result.append(equipment)

    return result


def _school_map(db: Session, school_ids: set[int]) -> dict[int, Escola]:
    if not school_ids:
        return {}

    schools = db.query(Escola).filter(Escola.id.in_(school_ids)).all()
    return {school.id: school for school in schools}


def _recent_transfer_count(
    db: Session,
    school_ids: set[int],
    equipment_ids: list[int],
    period_start: datetime,
    period_end: datetime,
) -> int:
    if not school_ids:
        return 0

    query = (
        db.query(Movement)
        .filter(Movement.movimentado_em >= period_start)
        .filter(Movement.movimentado_em <= period_end)
        .filter(
            or_(
                Movement.escola_origem_id.in_(school_ids),
                Movement.escola_destino_id.in_(school_ids),
            )
        )
    )
    if equipment_ids:
        query = query.filter(Movement.equipamento_id.in_(equipment_ids))

    return query.count()


def get_reports_overview(
    db: Session,
    current_user: dict,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    stale_days: int = 180,
    school_ids: list[int] | None = None,
    equipment_ids: list[int] | None = None,
    statuses: list[str] | None = None,
) -> dict:
    _ensure_can_view_reports(current_user)

    now = _now_naive()
    period_end = period_end or now
    period_start = period_start or (period_end - timedelta(days=30))
    cutoff = now - timedelta(days=stale_days)

    equipments = _filtered_visible_equipments(
        db=db,
        current_user=current_user,
        school_ids=school_ids,
        equipment_ids=equipment_ids,
        statuses=statuses,
    )
    visible_school_ids = _visible_school_ids(db, current_user)
    selected_school_ids = set(school_ids or [])
    report_school_ids = {equipment.escola_atual_id for equipment in equipments}
    transfer_scope_school_ids = selected_school_ids or report_school_ids or visible_school_ids
    equipment_ids = [equipment.id for equipment in equipments]
    schools = _school_map(db, report_school_ids | visible_school_ids)

    totals_by_school: dict[int, int] = {}
    totals_by_status = {status.value: 0 for status in EquipmentStatus}
    defect_statuses = {EquipmentStatus.DEFEITUOSO.value, EquipmentStatus.INOPERANTE.value}
    defective_by_school: dict[int, int] = {}

    for equipment in equipments:
        totals_by_school[equipment.escola_atual_id] = totals_by_school.get(equipment.escola_atual_id, 0) + 1
        status = equipment.status.value if hasattr(equipment.status, "value") else str(equipment.status)
        totals_by_status[status] = totals_by_status.get(status, 0) + 1
        if status in defect_statuses:
            defective_by_school[equipment.escola_atual_id] = defective_by_school.get(equipment.escola_atual_id, 0) + 1

    last_movements: dict[int, datetime | None] = {}
    if equipment_ids:
        rows = (
            db.query(
                Movement.equipamento_id,
                func.max(Movement.movimentado_em).label("last_movement_at"),
            )
            .filter(Movement.equipamento_id.in_(equipment_ids))
            .group_by(Movement.equipamento_id)
            .all()
        )
        last_movements = {equipment_id: last_movement_at for equipment_id, last_movement_at in rows}

    stale_equipments = []
    for equipment in equipments:
        last_movement_at = last_movements.get(equipment.id)
        if last_movement_at is not None and last_movement_at >= cutoff:
            continue

        school = schools.get(equipment.escola_atual_id)
        days_without_movement = (now - last_movement_at).days if last_movement_at else None
        stale_equipments.append(
            {
                "equipment_id": equipment.id,
                "patrimonio": equipment.patrimonio,
                "codigo_interno": equipment.codigo_interno,
                "tipo": equipment.tipo,
                "school_id": equipment.escola_atual_id,
                "school_name": school.nome if school else f"Escola #{equipment.escola_atual_id}",
                "last_movement_at": last_movement_at,
                "days_without_movement": days_without_movement,
            }
        )

    maintenance_items = []
    for equipment in equipments:
        status = equipment.status.value if hasattr(equipment.status, "value") else str(equipment.status)
        if status != EquipmentStatus.EM_MANUTENCAO.value:
            continue

        school = schools.get(equipment.escola_atual_id)
        maintenance_items.append(
            {
                "equipment_id": equipment.id,
                "patrimonio": equipment.patrimonio,
                "codigo_interno": equipment.codigo_interno,
                "tipo": equipment.tipo,
                "marca": equipment.marca,
                "modelo": equipment.modelo,
                "school_id": equipment.escola_atual_id,
                "school_name": school.nome if school else f"Escola #{equipment.escola_atual_id}",
                "sala_atual": equipment.sala_atual,
                "atualizado_em": equipment.atualizado_em,
            }
        )

    recent_transfers = _recent_transfer_count(db, transfer_scope_school_ids, equipment_ids, period_start, period_end)

    return {
        "summary": {
            "total_equipments": len(equipments),
            "total_schools": len(selected_school_ids or report_school_ids),
            "in_use": totals_by_status.get(EquipmentStatus.EM_USO.value, 0),
            "available": totals_by_status.get(EquipmentStatus.DISPONIVEL.value, 0),
            "maintenance": totals_by_status.get(EquipmentStatus.EM_MANUTENCAO.value, 0),
            "defective": sum(totals_by_status.get(status, 0) for status in defect_statuses),
            "in_transfer": totals_by_status.get(EquipmentStatus.EM_TRANSFERENCIA.value, 0),
            "discarded": totals_by_status.get(EquipmentStatus.DESCARTADO.value, 0),
            "recent_transfers": recent_transfers,
            "stale_equipments": len(stale_equipments),
        },
        "equipments_by_school": [
            {
                "school_id": school_id,
                "school_name": schools[school_id].nome if school_id in schools else f"Escola #{school_id}",
                "school_code": schools[school_id].codigo if school_id in schools else "-",
                "total": total,
            }
            for school_id, total in sorted(totals_by_school.items(), key=lambda item: item[1], reverse=True)
        ],
        "equipments_by_status": [
            {"status": status, "total": total}
            for status, total in sorted(totals_by_status.items(), key=lambda item: item[1], reverse=True)
            if total > 0
        ],
        "maintenance_items": sorted(
            maintenance_items,
            key=lambda item: item["atualizado_em"] or datetime.min,
        )[:50],
        "transfers_by_period": {
            "period_start": period_start,
            "period_end": period_end,
            "total": recent_transfers,
        },
        "schools_with_most_defects": [
            {
                "school_id": school_id,
                "school_name": schools[school_id].nome if school_id in schools else f"Escola #{school_id}",
                "school_code": schools[school_id].codigo if school_id in schools else "-",
                "defective_total": total,
            }
            for school_id, total in sorted(defective_by_school.items(), key=lambda item: item[1], reverse=True)
        ][:10],
        "stale_equipments": sorted(
            stale_equipments,
            key=lambda item: item["last_movement_at"] or datetime.min,
        )[:50],
    }


def _slice_overview_for_report(overview: dict, report_type: str):
    mapping = {
        "general_summary": overview["summary"],
        "equipments_by_school": overview["equipments_by_school"],
        "equipments_by_status": overview["equipments_by_status"],
        "maintenance_items": overview["maintenance_items"],
        "transfers_by_period": overview["transfers_by_period"],
        "schools_with_most_defects": overview["schools_with_most_defects"],
        "stale_equipments": overview["stale_equipments"],
    }

    if report_type not in mapping:
        raise HTTPException(status_code=422, detail="Tipo de relatorio invalido")

    return mapping[report_type]


def create_saved_report(db: Session, current_user: dict, data) -> SavedReport:
    _ensure_can_view_reports(current_user)

    title = data.titulo.strip()
    if not title:
        title = REPORT_TYPE_LABELS[data.tipo]

    overview = get_reports_overview(
        db=db,
        current_user=current_user,
        period_start=data.period_start,
        period_end=data.period_end,
        stale_days=data.stale_days,
        school_ids=data.school_ids,
        equipment_ids=data.equipment_ids,
        statuses=data.statuses,
    )
    result = _slice_overview_for_report(overview, data.tipo)

    saved_report = SavedReport(
        titulo=title[:140],
        tipo=data.tipo,
        parametros=jsonable_encoder(
            {
                "period_start": data.period_start,
                "period_end": data.period_end,
                "stale_days": data.stale_days,
                "school_ids": data.school_ids,
                "equipment_ids": data.equipment_ids,
                "statuses": data.statuses,
            }
        ),
        resultado=jsonable_encoder(result),
        criado_por_id=current_user["id"],
    )
    db.add(saved_report)
    db.commit()
    db.refresh(saved_report)
    return saved_report


def list_saved_reports(db: Session, current_user: dict, q: str | None = None) -> list[SavedReport]:
    _ensure_can_view_reports(current_user)

    query = db.query(SavedReport)
    if current_user["role"] != UserRole.SUPER_ADMIN:
        query = query.filter(SavedReport.criado_por_id == current_user["id"])

    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(SavedReport.titulo.ilike(pattern), SavedReport.tipo.ilike(pattern)))

    return query.order_by(SavedReport.criado_em.desc()).limit(100).all()


def get_saved_report(db: Session, report_id: int, current_user: dict) -> SavedReport:
    _ensure_can_view_reports(current_user)

    report = db.query(SavedReport).filter(SavedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Relatorio nao encontrado")

    if not _can_access_saved_report(report, current_user):
        raise HTTPException(status_code=403, detail="Sem acesso a este relatorio")

    return report


def delete_saved_report(db: Session, report_id: int, current_user: dict) -> None:
    report = get_saved_report(db, report_id, current_user)
    db.delete(report)
    db.commit()


def share_saved_report(db: Session, report_id: int, current_user: dict) -> SavedReport:
    report = get_saved_report(db, report_id, current_user)
    if not report.compartilhamento_token:
        report.compartilhamento_token = uuid4().hex
        db.commit()
        db.refresh(report)

    return report


def get_shared_report(db: Session, token: str) -> SavedReport:
    report = (
        db.query(SavedReport)
        .filter(SavedReport.compartilhamento_token == token)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Relatorio compartilhado nao encontrado")

    return report


def _flatten_row(prefix: str, value, row: dict) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            _flatten_row(f"{prefix}{key}.", nested, row)
        return

    row[prefix[:-1]] = value


def report_to_csv(report: SavedReport) -> str:
    result = report.resultado
    rows = result if isinstance(result, list) else [result]
    flat_rows = []

    for item in rows:
        row = {}
        if isinstance(item, dict):
            _flatten_row("", item, row)
        else:
            row["valor"] = item
        flat_rows.append(row)

    if not flat_rows:
        return ""

    fieldnames = sorted({key for row in flat_rows for key in row.keys()})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(flat_rows)
    return output.getvalue()
