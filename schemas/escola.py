from pydantic import BaseModel


class EscolaBase(BaseModel):
    nome: str
    codigo: str
    endereco: str | None = None


class EscolaCreate(EscolaBase):
    pass


class EscolaUpdate(BaseModel):
    nome: str | None = None
    codigo: str | None = None
    endereco: str | None = None


class EscolaResponse(EscolaBase):
    id: int

    model_config = {"from_attributes": True}
