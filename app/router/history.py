from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database.database import get_db
from models.equipment_history import EquipmentHistory
from services.equipment_service import get_equipment

router = APIRouter(prefix="/equipments", tags=["Historico"])


@router.get("/{equipment_id}/history")
def get_equipment_history(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    get_equipment(db, equipment_id, current_user)

    return (
        db.query(EquipmentHistory)
        .filter(EquipmentHistory.equipamento_id == equipment_id)
        .order_by(EquipmentHistory.criado_em.desc())
        .all()
    )
