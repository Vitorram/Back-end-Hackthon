import hashlib
import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from constants import EquipmentStatus
from core.roles import UserRole
from models.escola import Escola
from repositories import equipment_repository
from schemas.equipment import EquipmentCreate, EquipmentStatusUpdate, EquipmentUpdate
from services.history_service import log_history

VALID_STATUSES = {
    EquipmentStatus.EM_USO,
    EquipmentStatus.EM_MANUTENCAO,
    EquipmentStatus.DEFEITUOSO,
    EquipmentStatus.DESCARTADO,
    EquipmentStatus.DISPONIVEL,
    EquipmentStatus.INOPERANTE,
    EquipmentStatus.EM_TRANSFERENCIA,
}

ALLOWED_EQUIPMENT_TYPES = {
    "Computadores",
    "Notebooks",
    "Tablets",
    "Impressoras",
    "Projetores",
    "Dispositivos de conectividade",
}

EQUIPMENT_TYPE_ALIASES = {
    "computador": "Computadores",
    "computadores": "Computadores",
    "desktop": "Computadores",
    "pc": "Computadores",
    "monitor": "Computadores",
    "notebook": "Notebooks",
    "notebooks": "Notebooks",
    "laptop": "Notebooks",
    "tablet": "Tablets",
    "tablets": "Tablets",
    "impressora": "Impressoras",
    "impressoras": "Impressoras",
    "printer": "Impressoras",
    "projetor": "Projetores",
    "projetores": "Projetores",
    "projector": "Projetores",
    "datashow": "Projetores",
    "roteador": "Dispositivos de conectividade",
    "switch": "Dispositivos de conectividade",
    "access point": "Dispositivos de conectividade",
    "ap": "Dispositivos de conectividade",
    "wifi": "Dispositivos de conectividade",
    "rede": "Dispositivos de conectividade",
    "conectividade": "Dispositivos de conectividade",
}

ALLOWED_TRANSITIONS = {
    EquipmentStatus.EM_USO: [
        EquipmentStatus.DEFEITUOSO,
        EquipmentStatus.EM_TRANSFERENCIA,
        EquipmentStatus.DISPONIVEL,
    ],
    EquipmentStatus.DEFEITUOSO: [
        EquipmentStatus.EM_MANUTENCAO,
    ],
    EquipmentStatus.EM_MANUTENCAO: [
        EquipmentStatus.EM_USO,
        EquipmentStatus.INOPERANTE,
    ],
    EquipmentStatus.EM_TRANSFERENCIA: [
        EquipmentStatus.EM_USO,
    ],
    EquipmentStatus.DISPONIVEL: [
        EquipmentStatus.EM_USO,
    ],
    EquipmentStatus.INOPERANTE: [
        EquipmentStatus.DESCARTADO,
    ],
    EquipmentStatus.DESCARTADO: [],
}


def _can_manage_equipment(user: dict, escola_id: int | None) -> bool:
    if user["role"] == UserRole.SUPER_ADMIN:
        return True

    permissions = user.get("permissions", {})
    if not permissions.get("pode_editar_equipamento"):
        return False

    if user["role"] == UserRole.MANAGER:
        return escola_id is None or user.get("school_id") == escola_id

    return False


def _can_create_equipment(user: dict, escola_id: int | None) -> bool:
    if user["role"] == UserRole.SUPER_ADMIN:
        return True

    permissions = user.get("permissions", {})
    if not (
        permissions.get("pode_criar_equipamento")
        or permissions.get("pode_editar_equipamento")
    ):
        return False

    user_school_id = user.get("school_id")
    if user["role"] == UserRole.MANAGER and user_school_id is None:
        return True

    return escola_id is None or user_school_id == escola_id


def _can_view_equipment(user: dict, escola_id: int | None) -> bool:
    if user["role"] == UserRole.SUPER_ADMIN:
        return True

    return escola_id is None or user.get("school_id") == escola_id


def _validate_status(status: str | None) -> None:
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Status de equipamento invalido")


def _normalize_type(tipo: str | None) -> str | None:
    if tipo is None:
        return None

    clean_tipo = tipo.strip()
    if clean_tipo in ALLOWED_EQUIPMENT_TYPES:
        return clean_tipo

    normalized = unicodedata.normalize("NFKD", clean_tipo).encode("ascii", "ignore").decode("ascii").lower()
    return EQUIPMENT_TYPE_ALIASES.get(normalized)


def _validate_type(tipo: str | None) -> None:
    if tipo is not None and tipo not in ALLOWED_EQUIPMENT_TYPES:
        raise HTTPException(status_code=422, detail="Categoria de equipamento invalida")


def _status_value(status) -> EquipmentStatus:
    if isinstance(status, EquipmentStatus):
        return status

    return EquipmentStatus(status)


def _validate_status_transition(current_status: str, next_status: str) -> None:
    current = _status_value(current_status)
    next_ = _status_value(next_status)

    if current == next_:
        return

    if next_ not in ALLOWED_TRANSITIONS.get(current, []):
        raise HTTPException(
            status_code=409,
            detail=f"Transicao de status nao permitida: {current.value} -> {next_.value}",
        )


def _slug_part(value: str | None, fallback: str) -> str:
    raw = value or fallback
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", normalized).strip("-").upper()
    return slug or fallback


def _build_identifier(db: Session, data: EquipmentCreate) -> str:
    school = db.query(Escola).filter(Escola.id == data.escola_atual_id).first()
    school_part = _slug_part(school.nome if school else None, "ESCOLA")
    type_part = _slug_part(data.tipo, "EQUIP")
    serial_part = _slug_part(data.numero_serie, "SEM-SERIE")
    fingerprint = hashlib.sha1(f"{school_part}|{type_part}|{serial_part}".encode("utf-8")).hexdigest()[:6].upper()
    stem = f"{school_part}-{type_part}-{serial_part}"
    base = f"{stem[:43].strip('-')}-{fingerprint}"

    candidate = base
    sequence = 2
    while equipment_repository.get_equipment_by_patrimonio(db, candidate):
        suffix = f"-{sequence}"
        candidate = f"{base[:50 - len(suffix)]}{suffix}"
        sequence += 1

    return candidate


def list_equipments(db: Session, current_user: dict):
    equipments = equipment_repository.list_equipments(db)
    return [
        equipment
        for equipment in equipments
        if _can_view_equipment(current_user, equipment.escola_atual_id)
    ]


def get_equipment(db: Session, equipment_id: int, current_user: dict):
    equipment = equipment_repository.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipamento nao encontrado")

    if not _can_view_equipment(current_user, equipment.escola_atual_id):
        raise HTTPException(status_code=403, detail="Sem acesso a este equipamento")

    return equipment


def create_equipment(db: Session, data: EquipmentCreate, current_user: dict):
    _validate_status(data.status)
    normalized_type = _normalize_type(data.tipo)
    if normalized_type is None:
        raise HTTPException(status_code=422, detail="Categoria de equipamento invalida")
    _validate_type(normalized_type)
    data = data.model_copy(update={"tipo": normalized_type})

    if not _can_create_equipment(current_user, data.escola_atual_id):
        raise HTTPException(status_code=403, detail="Sem permissao para criar equipamento")

    patrimonio = (data.patrimonio or "").strip() or _build_identifier(db, data)
    codigo_interno = (data.codigo_interno or "").strip() or patrimonio
    data = data.model_copy(update={"patrimonio": patrimonio, "codigo_interno": codigo_interno})

    if equipment_repository.get_equipment_by_patrimonio(db, data.patrimonio):
        raise HTTPException(status_code=409, detail="Patrimonio ja cadastrado")

    if equipment_repository.get_equipment_by_codigo_interno(db, data.codigo_interno):
        raise HTTPException(status_code=409, detail="Codigo interno ja cadastrado")

    return equipment_repository.create_equipment(db, data)


def update_equipment(
    db: Session,
    equipment_id: int,
    data: EquipmentUpdate,
    current_user: dict,
):
    equipment = get_equipment(db, equipment_id, current_user)
    target_school_id = (
        data.escola_atual_id
        if data.escola_atual_id is not None
        else equipment.escola_atual_id
    )

    _validate_status(data.status)
    if data.tipo is not None:
        normalized_type = _normalize_type(data.tipo)
        if normalized_type is None:
            raise HTTPException(status_code=422, detail="Categoria de equipamento invalida")
        _validate_type(normalized_type)
        data = data.model_copy(update={"tipo": normalized_type})

    if not _can_manage_equipment(current_user, equipment.escola_atual_id):
        raise HTTPException(status_code=403, detail="Sem permissao para editar equipamento")

    if target_school_id != equipment.escola_atual_id:
        if not current_user.get("permissions", {}).get("pode_transferir"):
            raise HTTPException(status_code=403, detail="Sem permissao para transferir")

        if not _can_manage_equipment(current_user, target_school_id):
            raise HTTPException(status_code=403, detail="Sem acesso a escola de destino")

    if data.patrimonio and data.patrimonio != equipment.patrimonio:
        existing = equipment_repository.get_equipment_by_patrimonio(db, data.patrimonio)
        if existing:
            raise HTTPException(status_code=409, detail="Patrimonio ja cadastrado")

    if data.codigo_interno and data.codigo_interno != equipment.codigo_interno:
        existing = equipment_repository.get_equipment_by_codigo_interno(
            db,
            data.codigo_interno,
        )
        if existing:
            raise HTTPException(status_code=409, detail="Codigo interno ja cadastrado")

    return equipment_repository.update_equipment(db, equipment, data)


def update_equipment_status(
    db: Session,
    equipment_id: int,
    data: EquipmentStatusUpdate,
    current_user: dict,
):
    equipment = get_equipment(db, equipment_id, current_user)

    if not _can_manage_equipment(current_user, equipment.escola_atual_id):
        raise HTTPException(status_code=403, detail="Sem permissao para alterar status")

    _validate_status(data.status)
    _validate_status_transition(equipment.status, data.status)

    old_status = _status_value(equipment.status).value
    new_status = _status_value(data.status).value
    equipment.status = new_status

    motivo = data.motivo or "Nao informado"
    log_history(
        db=db,
        equipment_id=equipment.id,
        user_id=current_user["id"],
        event_type="ATUALIZADO",
        description=(
            f"Status alterado de {old_status} para {new_status}. "
            f"Motivo: {motivo}"
        ),
    )

    db.commit()
    db.refresh(equipment)
    return equipment


def delete_equipment(db: Session, equipment_id: int, current_user: dict) -> None:
    equipment = get_equipment(db, equipment_id, current_user)

    if not _can_manage_equipment(current_user, equipment.escola_atual_id):
        raise HTTPException(status_code=403, detail="Sem permissao para remover equipamento")

    equipment_repository.delete_equipment(db, equipment)
