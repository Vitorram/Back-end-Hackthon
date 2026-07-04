from sqlalchemy.orm import Session

from models.equipment_history import EquipmentHistory


def log_history(
    db: Session,
    equipment_id: int,
    user_id: int | None,
    event_type: str,
    description: str,
):
    history = EquipmentHistory(
        equipamento_id=equipment_id,
        usuario_id=user_id,
        tipo_evento=event_type,
        descricao=description,
    )

    db.add(history)
    return history
