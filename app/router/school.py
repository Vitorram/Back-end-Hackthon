from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_super_admin
from database.database import get_db
from models.escola import Escola
from schemas.escola import EscolaCreate, EscolaResponse, EscolaUpdate

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.get("", response_model=list[EscolaResponse])
def list_schools(
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Escola).order_by(Escola.nome.asc()).all()


@router.get("/{school_id}", response_model=EscolaResponse)
def get_school(
    school_id: int,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    school = db.query(Escola).filter(Escola.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola nao encontrada")
    return school


@router.post("", response_model=EscolaResponse, status_code=status.HTTP_201_CREATED)
def create_school(
    data: EscolaCreate,
    _: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(Escola).filter(Escola.codigo == data.codigo).first()
    if existing:
        raise HTTPException(status_code=409, detail="Codigo de escola ja cadastrado")

    school = Escola(**data.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


@router.put("/{school_id}", response_model=EscolaResponse)
def update_school(
    school_id: int,
    data: EscolaUpdate,
    _: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    school = db.query(Escola).filter(Escola.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola nao encontrada")

    if data.codigo and data.codigo != school.codigo:
        existing = db.query(Escola).filter(Escola.codigo == data.codigo).first()
        if existing:
            raise HTTPException(status_code=409, detail="Codigo de escola ja cadastrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(school, field, value)

    db.commit()
    db.refresh(school)
    return school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    _: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    school = db.query(Escola).filter(Escola.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola nao encontrada")

    db.delete(school)
    db.commit()
