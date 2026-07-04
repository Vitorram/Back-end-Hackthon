from sqlalchemy.orm import Session

from models.equipment import Equipment
from schemas.equipment import EquipmentCreate, EquipmentUpdate


def list_equipments(db: Session) -> list[Equipment]:
    return db.query(Equipment).order_by(Equipment.id.asc()).all()


def get_equipment(db: Session, equipment_id: int) -> Equipment | None:
    return db.query(Equipment).filter(Equipment.id == equipment_id).first()


def get_equipment_by_patrimonio(db: Session, patrimonio: str) -> Equipment | None:
    return db.query(Equipment).filter(Equipment.patrimonio == patrimonio).first()


def get_equipment_by_codigo_interno(db: Session, codigo_interno: str) -> Equipment | None:
    return db.query(Equipment).filter(Equipment.codigo_interno == codigo_interno).first()


def create_equipment(db: Session, data: EquipmentCreate) -> Equipment:
    equipment = Equipment(**data.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


def update_equipment(
    db: Session,
    equipment: Equipment,
    data: EquipmentUpdate,
) -> Equipment:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)
    return equipment


def delete_equipment(db: Session, equipment: Equipment) -> None:
    db.delete(equipment)
    db.commit()
