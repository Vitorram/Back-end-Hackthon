from pydantic import BaseModel


class TransferEquipmentRequest(BaseModel):
    escola_destino_id: int
    sala_destino: str | None = None
    motivo: str | None = None
