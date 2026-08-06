from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user
from backend.database.database import get_db
from backend.schemas.movement import TransferEquipmentRequest
from backend.services.movement_service import transfer_equipment

router = APIRouter(prefix="/equipments", tags=["Movimentacoes"])


@router.post("/{equipment_id}/transfer")
def transfer(
    equipment_id: int,
    data: TransferEquipmentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return transfer_equipment(db, equipment_id, data, current_user)
