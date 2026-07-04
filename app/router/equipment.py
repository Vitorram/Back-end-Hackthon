from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database.database import get_db
from schemas.equipment import (
    EquipmentCreate,
    EquipmentResponse,
    EquipmentStatusUpdate,
    EquipmentUpdate,
)
from services import equipment_service

router = APIRouter(prefix="/equipments", tags=["Equipments"])


@router.get("", response_model=list[EquipmentResponse])
def list_equipments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return equipment_service.list_equipments(db, current_user)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return equipment_service.get_equipment(db, equipment_id, current_user)


@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return equipment_service.create_equipment(db, data, current_user)


@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return equipment_service.update_equipment(db, equipment_id, data, current_user)


@router.patch("/{equipment_id}/status", response_model=EquipmentResponse)
def update_equipment_status(
    equipment_id: int,
    data: EquipmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return equipment_service.update_equipment_status(
        db,
        equipment_id,
        data,
        current_user,
    )


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    equipment_service.delete_equipment(db, equipment_id, current_user)
