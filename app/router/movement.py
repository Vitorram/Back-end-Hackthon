from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database.database import get_db
from schemas.movement import TransferEquipmentRequest
from services.movement_service import transfer_equipment

router = APIRouter(prefix="/equipments", tags=["Movimentacoes"])


@router.post("/{equipment_id}/transfer")
def transfer(
    equipment_id: int,
    data: TransferEquipmentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return transfer_equipment(db, equipment_id, data, current_user)
