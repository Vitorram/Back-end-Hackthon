from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from database.database import Base
from models.equipment import Equipment  # noqa: F401
from models.escola import Escola  # noqa: F401
from models.usuario import Usuario  # noqa: F401


class Movement(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    equipamento_id = Column(Integer, ForeignKey("equipamentos.id"), nullable=False)
    escola_origem_id = Column(Integer, ForeignKey("escolas.id"), nullable=True)
    escola_destino_id = Column(Integer, ForeignKey("escolas.id"), nullable=False)
    motivo = Column(String(255), nullable=True)
    usuario_responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    status = Column(String(30), nullable=True)
    movimentado_em = Column(DateTime, server_default=func.now())
