from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from database.database import Base
from models.equipment import Equipment  # noqa: F401
from models.usuario import Usuario  # noqa: F401


class EquipmentHistory(Base):
    __tablename__ = "historico_equipamentos"

    id = Column(Integer, primary_key=True, index=True)
    equipamento_id = Column(Integer, ForeignKey("equipamentos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo_evento = Column(
        Enum(
            "CRIADO",
            "ATUALIZADO",
            "TRANSFERIDO",
            "CHAMADO_ABERTO",
            "MANUTENCAO_INICIADA",
            "MANUTENCAO_FINALIZADA",
            "DESCARTADO",
        ),
        nullable=False,
    )
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
