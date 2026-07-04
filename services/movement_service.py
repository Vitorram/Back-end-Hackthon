from fastapi import HTTPException
from sqlalchemy.orm import Session

from constants import EquipmentStatus
from core.roles import UserRole
from models.equipment import Equipment
from models.escola import Escola
from models.movement import Movement
from services.history_service import log_history


def _can_transfer(current_user: dict, origem_id: int | None, destino_id: int) -> bool:
    if current_user["role"] == UserRole.SUPER_ADMIN:
        return True

    if not current_user.get("permissions", {}).get("pode_transferir"):
        return False

    if current_user["role"] != UserRole.MANAGER:
        return False

    user_school_id = current_user.get("school_id")
    return user_school_id in (origem_id, destino_id)


def transfer_equipment(
    db: Session,
    equipment_id: int,
    data,
    current_user: dict,
):
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipamento nao encontrado")

    destination_school = (
        db.query(Escola)
        .filter(Escola.id == data.escola_destino_id)
        .first()
    )
    if not destination_school:
        raise HTTPException(status_code=404, detail="Escola de destino nao encontrada")

    origem_id = equipment.escola_atual_id

    if not _can_transfer(current_user, origem_id, data.escola_destino_id):
        raise HTTPException(
            status_code=403,
            detail="Usuario sem permissao para transferir equipamentos",
        )

    equipment.escola_atual_id = data.escola_destino_id
    equipment.sala_atual = data.sala_destino
    equipment.status = EquipmentStatus.EM_TRANSFERENCIA

    movement = Movement(
        equipamento_id=equipment.id,
        escola_origem_id=origem_id,
        escola_destino_id=data.escola_destino_id,
        motivo=data.motivo,
        usuario_responsavel_id=current_user["id"],
        status="CONCLUIDA",
    )

    motivo = data.motivo or "Nao informado"
    log_history(
        db=db,
        equipment_id=equipment.id,
        user_id=current_user["id"],
        event_type="TRANSFERIDO",
        description=(
            f"Equipamento transferido da escola {origem_id} "
            f"para escola {data.escola_destino_id}. Motivo: {motivo}"
        ),
    )

    db.add(movement)
    db.commit()
    db.refresh(equipment)

    return {
        "message": "Transferencia realizada com sucesso",
        "equipment": equipment,
    }
