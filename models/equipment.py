from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from constants import EquipmentStatus
from database.database import Base
from models.escola import Escola  # noqa: F401


class Equipment(Base):
    __tablename__ = "equipamentos"

    id = Column(Integer, primary_key=True, index=True)
    patrimonio = Column(String(50), unique=True, nullable=True, index=True)
    codigo_interno = Column(String(50), unique=True, nullable=False, index=True)
    tipo = Column(String(80), nullable=False)
    marca = Column(String(80), nullable=True)
    modelo = Column(String(100), nullable=True)
    numero_serie = Column(String(100), nullable=True)
    data_aquisicao = Column(Date, nullable=True)
    status = Column(
        Enum(
            EquipmentStatus.EM_USO,
            EquipmentStatus.EM_MANUTENCAO,
            EquipmentStatus.DEFEITUOSO,
            EquipmentStatus.DESCARTADO,
            EquipmentStatus.DISPONIVEL,
            EquipmentStatus.INOPERANTE,
            EquipmentStatus.EM_TRANSFERENCIA,
        ),
        nullable=True,
        default=EquipmentStatus.EM_USO,
    )
    escola_atual_id = Column(Integer, ForeignKey("escolas.id"), nullable=False, index=True)
    sala_atual = Column(String(100), nullable=True)
    url_foto = Column(String(255), nullable=True)
    observacoes = Column(Text, nullable=True)
    adquirido_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
