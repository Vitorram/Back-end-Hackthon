from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from backend.database.database import Base
from backend.models.usuario import Usuario  # noqa: F401


class SavedReport(Base):
    __tablename__ = "relatorios_salvos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(140), nullable=False)
    tipo = Column(String(60), nullable=False, index=True)
    parametros = Column(JSON, nullable=False)
    resultado = Column(JSON, nullable=False)
    criado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    compartilhamento_token = Column(String(64), nullable=True, unique=True, index=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
