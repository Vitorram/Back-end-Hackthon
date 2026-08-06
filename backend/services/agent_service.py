import re
import unicodedata

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.models.equipment import Equipment
from backend.models.escola import Escola
from backend.models.equipment_history import EquipmentHistory
from backend.models.movement import Movement
from backend.models.usuario import Usuario
from backend.services import equipment_service

TYPE_ALIASES = {
    "tablet": "Tablets",
    "tablets": "Tablets",
    "notebook": "Notebooks",
    "notebooks": "Notebooks",
    "computador": "Computadores",
    "computadores": "Computadores",
    "pc": "Computadores",
    "pcs": "Computadores",
    "impressora": "Impressoras",
    "impressoras": "Impressoras",
    "projetor": "Projetores",
    "projetores": "Projetores",
    "rede": "Dispositivos de conectividade",
    "switch": "Dispositivos de conectividade",
    "roteador": "Dispositivos de conectividade",
}


def _datetime(value):
    return value.isoformat() if value else None


def _date(value):
    return value.isoformat() if value else None


def _status(value):
    return getattr(value, "value", value)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_value.lower()).strip()


def _detect_equipment_type(prompt: str) -> str:
    normalized = _normalize_text(prompt)
    for alias, equipment_type in TYPE_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", normalized):
            return equipment_type
    return "Tablets"


def _school_matches_prompt(school: Escola, normalized_prompt: str) -> bool:
    code = _normalize_text(school.codigo)
    name = _normalize_text(school.nome)
    if code and code in normalized_prompt:
        return True
    if name and name in normalized_prompt:
        return True

    words = [word for word in re.split(r"[^a-z0-9]+", name) if len(word) >= 4]
    ignored = {"emef", "emei", "prof", "profa", "professor", "professora"}
    relevant_words = [word for word in words if word not in ignored]
    hits = sum(1 for word in relevant_words if re.search(rf"\b{re.escape(word)}\b", normalized_prompt))
    return hits >= 2


def _equipment_payload(equipment: Equipment) -> dict:
    return {
        "id": equipment.id,
        "patrimonio": equipment.patrimonio,
        "codigo_interno": equipment.codigo_interno,
        "tipo": equipment.tipo,
        "marca": equipment.marca,
        "modelo": equipment.modelo,
        "numero_serie": equipment.numero_serie,
        "data_aquisicao": _date(equipment.data_aquisicao),
        "status": _status(equipment.status),
        "escola_atual_id": equipment.escola_atual_id,
        "sala_atual": equipment.sala_atual,
        "url_foto": equipment.url_foto,
        "observacoes": equipment.observacoes,
        "adquirido_em": _datetime(equipment.adquirido_em),
        "atualizado_em": _datetime(equipment.atualizado_em),
    }


def _school_payload(school: Escola) -> dict:
    return {
        "id": school.id,
        "nome": school.nome,
        "codigo": school.codigo,
        "endereco": school.endereco,
    }


def _user_payload(user: Usuario) -> dict:
    return {
        "id": user.id,
        "nome": user.nome,
        "matricula": user.matricula,
        "email": user.email,
        "perfil": user.perfil,
        "escola_id": user.escola_id,
        "ativo": bool(user.ativo),
        "aprovado": bool(user.aprovado),
        "ultimo_acesso": _datetime(user.ultimo_acesso),
        "permissoes": {
            "pode_ver_dashboard": bool(user.pode_ver_dashboard),
            "pode_transferir": bool(user.pode_transferir),
            "pode_criar_equipamento": bool(getattr(user, "pode_criar_equipamento", False)),
            "pode_editar_equipamento": bool(user.pode_editar_equipamento),
            "pode_abrir_chamado": bool(user.pode_abrir_chamado),
            "pode_gerenciar_usuarios": bool(user.pode_gerenciar_usuarios),
        },
    }


def _history_payload(history: EquipmentHistory) -> dict:
    return {
        "id": history.id,
        "equipamento_id": history.equipamento_id,
        "usuario_id": history.usuario_id,
        "tipo_evento": history.tipo_evento,
        "descricao": history.descricao,
        "criado_em": _datetime(history.criado_em),
    }


def _movement_payload(movement: Movement) -> dict:
    return {
        "id": movement.id,
        "equipamento_id": movement.equipamento_id,
        "escola_origem_id": movement.escola_origem_id,
        "escola_destino_id": movement.escola_destino_id,
        "motivo": movement.motivo,
        "usuario_responsavel_id": movement.usuario_responsavel_id,
        "status": movement.status,
        "movimentado_em": _datetime(movement.movimentado_em),
    }


def get_agent_summary(db: Session, current_user: dict | None = None) -> dict:
    if current_user:
        equipments = equipment_service.list_equipments(db, current_user)
        equipment_ids = [equipment.id for equipment in equipments]
        total_equipments = len(equipments)
        status_rows = {}
        type_rows = {}
        for equipment in equipments:
            status = _status(equipment.status) or "SEM_STATUS"
            status_rows[status] = status_rows.get(status, 0) + 1
            type_rows[equipment.tipo] = type_rows.get(equipment.tipo, 0) + 1
    else:
        total_equipments = db.query(func.count(Equipment.id)).scalar() or 0
        equipment_ids = None
        status_rows = dict(
            db.query(Equipment.status, func.count(Equipment.id))
            .group_by(Equipment.status)
            .all()
        )
        type_rows = dict(
            db.query(Equipment.tipo, func.count(Equipment.id))
            .group_by(Equipment.tipo)
            .all()
        )

    movement_query = db.query(func.count(Movement.id))
    history_query = db.query(func.count(EquipmentHistory.id))
    if equipment_ids is not None:
        if not equipment_ids:
            total_movements = 0
            total_history = 0
        else:
            total_movements = movement_query.filter(Movement.equipamento_id.in_(equipment_ids)).scalar() or 0
            total_history = history_query.filter(EquipmentHistory.equipamento_id.in_(equipment_ids)).scalar() or 0
    else:
        total_movements = movement_query.scalar() or 0
        total_history = history_query.scalar() or 0

    return {
        "equipamentos": {
            "total": total_equipments,
            "por_status": {_status(status): count for status, count in status_rows.items()},
            "por_tipo": type_rows,
        },
        "escolas": db.query(func.count(Escola.id)).scalar() or 0,
        "usuarios": db.query(func.count(Usuario.id)).scalar() or 0,
        "movimentacoes": total_movements,
        "historicos": total_history,
    }


def search_agent_data(
    db: Session,
    query: str,
    current_user: dict | None = None,
    limit: int = 10,
    include_users: bool = True,
) -> dict:
    term = f"%{query.strip()}%"
    if term == "%%":
        return {"equipamentos": [], "escolas": [], "usuarios": []}

    if current_user:
        visible_equipments = equipment_service.list_equipments(db, current_user)
        visible_ids = [equipment.id for equipment in visible_equipments]
        equipment_query = db.query(Equipment).filter(Equipment.id.in_(visible_ids)) if visible_ids else None
    else:
        equipment_query = db.query(Equipment)

    equipments = []
    if equipment_query is not None:
        equipments = (
            equipment_query.filter(
                or_(
                    Equipment.patrimonio.ilike(term),
                    Equipment.codigo_interno.ilike(term),
                    Equipment.tipo.ilike(term),
                    Equipment.marca.ilike(term),
                    Equipment.modelo.ilike(term),
                    Equipment.numero_serie.ilike(term),
                    Equipment.sala_atual.ilike(term),
                )
            )
            .order_by(Equipment.id.desc())
            .limit(limit)
            .all()
        )

    schools = (
        db.query(Escola)
        .filter(or_(Escola.nome.ilike(term), Escola.codigo.ilike(term), Escola.endereco.ilike(term)))
        .order_by(Escola.nome.asc())
        .limit(limit)
        .all()
    )
    users = []
    if include_users:
        users = (
            db.query(Usuario)
            .filter(or_(Usuario.nome.ilike(term), Usuario.email.ilike(term), Usuario.matricula.ilike(term)))
            .order_by(Usuario.nome.asc())
            .limit(limit)
            .all()
        )

    return {
        "equipamentos": [_equipment_payload(equipment) for equipment in equipments],
        "escolas": [_school_payload(school) for school in schools],
        "usuarios": [_user_payload(user) for user in users],
    }


def find_user(db: Session, login: str) -> dict:
    value = login.strip()
    user = (
        db.query(Usuario)
        .filter(or_(Usuario.email == value, Usuario.matricula == value, Usuario.nome.ilike(f"%{value}%")))
        .first()
    )
    if not user:
        return {"erro": f"Usuario '{login}' nao encontrado."}
    return _user_payload(user)


def list_users(db: Session, only_active: bool = False, limit: int = 50) -> list[dict]:
    query = db.query(Usuario)
    if only_active:
        query = query.filter(Usuario.ativo == True)  # noqa: E712
    users = query.order_by(Usuario.nome.asc()).limit(limit).all()
    return [_user_payload(user) for user in users]


def find_equipment(db: Session, identifier: str, current_user: dict | None = None) -> dict:
    value = identifier.strip()
    query = db.query(Equipment).filter(
        or_(
            Equipment.patrimonio == value,
            Equipment.codigo_interno == value,
            Equipment.numero_serie == value,
        )
    )
    equipment = query.first()

    if not equipment and value.isdigit():
        equipment = db.query(Equipment).filter(Equipment.id == int(value)).first()

    if not equipment:
        return {"erro": f"Equipamento '{identifier}' nao encontrado."}

    if current_user and not equipment_service._can_view_equipment(current_user, equipment.escola_atual_id):
        return {"erro": "Sem acesso a este equipamento."}

    school = db.query(Escola).filter(Escola.id == equipment.escola_atual_id).first()
    history = (
        db.query(EquipmentHistory)
        .filter(EquipmentHistory.equipamento_id == equipment.id)
        .order_by(EquipmentHistory.criado_em.desc())
        .limit(5)
        .all()
    )
    movements = (
        db.query(Movement)
        .filter(Movement.equipamento_id == equipment.id)
        .order_by(Movement.movimentado_em.desc())
        .limit(5)
        .all()
    )

    return {
        **_equipment_payload(equipment),
        "escola_atual": _school_payload(school) if school else None,
        "ultimos_historicos": [_history_payload(item) for item in history],
        "ultimas_movimentacoes": [_movement_payload(item) for item in movements],
    }


def list_equipments_by_school(
    db: Session,
    school_id: int,
    current_user: dict | None = None,
    limit: int = 50,
) -> list[dict]:
    query = db.query(Equipment).filter(Equipment.escola_atual_id == school_id)
    equipments = query.order_by(Equipment.id.asc()).limit(limit).all()
    if current_user:
        equipments = [
            equipment
            for equipment in equipments
            if equipment_service._can_view_equipment(current_user, equipment.escola_atual_id)
        ]
    return [_equipment_payload(equipment) for equipment in equipments]


def generate_equipment_report(
    db: Session,
    prompt: str,
    current_user: dict | None = None,
) -> dict:
    equipment_type = _detect_equipment_type(prompt)
    normalized_prompt = _normalize_text(prompt)
    schools = db.query(Escola).order_by(Escola.nome.asc()).all()
    selected_schools = [
        school
        for school in schools
        if _school_matches_prompt(school, normalized_prompt)
    ]

    if not selected_schools:
        selected_schools = schools

    rows = []
    totals_by_status: dict[str, int] = {}
    total = 0

    for school in selected_schools:
        if current_user and not equipment_service._can_view_equipment(current_user, school.id):
            continue

        equipments = (
            db.query(Equipment)
            .filter(Equipment.escola_atual_id == school.id, Equipment.tipo == equipment_type)
            .all()
        )
        by_status: dict[str, int] = {}
        for equipment in equipments:
            status = _status(equipment.status) or "SEM_STATUS"
            by_status[status] = by_status.get(status, 0) + 1
            totals_by_status[status] = totals_by_status.get(status, 0) + 1

        amount = len(equipments)
        total += amount
        rows.append(
            {
                "escola_id": school.id,
                "escola": school.nome,
                "codigo": school.codigo,
                "bairro": school.endereco,
                "tipo": equipment_type,
                "quantidade": amount,
                "por_status": by_status,
            }
        )

    rows.sort(key=lambda item: item["quantidade"], reverse=True)
    average = round(total / len(rows), 1) if rows else 0
    attention = sum(totals_by_status.get(status, 0) for status in ["EM_MANUTENCAO", "DEFEITUOSO", "INOPERANTE"])

    markdown_lines = [
        f"Relatorio SIGTEC: {equipment_type}",
        f"Total encontrado: {total}",
        f"Escolas analisadas: {len(rows)}",
        f"Media por escola: {average}",
        f"Itens que precisam de atencao: {attention}",
        "",
        "Detalhamento por escola:",
    ]
    for row in rows:
        status_text = ", ".join(f"{status}: {count}" for status, count in row["por_status"].items()) or "sem itens"
        markdown_lines.append(f"- {row['escola']}: {row['quantidade']} ({status_text})")

    return {
        "pergunta": prompt,
        "tipo_detectado": equipment_type,
        "total": total,
        "media_por_escola": average,
        "itens_em_atencao": attention,
        "por_status": totals_by_status,
        "escolas": rows,
        "relatorio": "\n".join(markdown_lines),
    }
