from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from constants import EquipmentStatus

EquipmentStatusValue = Literal[
    "EM_USO",
    "EM_MANUTENCAO",
    "DEFEITUOSO",
    "DESCARTADO",
    "DISPONIVEL",
    "INOPERANTE",
    "EM_TRANSFERENCIA",
]


class EquipmentBase(BaseModel):
    patrimonio: str | None = None
    codigo_interno: str
    tipo: str
    marca: str | None = None
    modelo: str | None = None
    numero_serie: str | None = None
    data_aquisicao: date | None = None
    status: EquipmentStatusValue = EquipmentStatus.EM_USO
    escola_atual_id: int
    sala_atual: str | None = None
    url_foto: str | None = None
    observacoes: str | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    patrimonio: str | None = None
    codigo_interno: str | None = None
    tipo: str | None = None
    marca: str | None = None
    modelo: str | None = None
    numero_serie: str | None = None
    data_aquisicao: date | None = None
    status: EquipmentStatusValue | None = None
    escola_atual_id: int | None = None
    sala_atual: str | None = None
    url_foto: str | None = None
    observacoes: str | None = None


class EquipmentStatusUpdate(BaseModel):
    status: EquipmentStatusValue
    motivo: str | None = None


class EquipmentResponse(EquipmentBase):
    id: int
    adquirido_em: datetime | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}
