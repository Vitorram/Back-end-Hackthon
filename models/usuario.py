from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.database import Base
from models.escola import Escola  # noqa: F401


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    matricula = Column(String(30), unique=True, nullable=True)
    email = Column(String(120), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum("COMMON", "MANAGER", "SUPER_ADMIN"), nullable=False)
    escola_id = Column(Integer, ForeignKey("escolas.id"), nullable=True)
    ativo = Column(Boolean, default=True)
    aprovado = Column(Boolean, default=False)
    aprovado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    aprovado_em = Column(DateTime, nullable=True)
    ultimo_acesso = Column(DateTime, nullable=True)
    pode_ver_dashboard = Column(Boolean, default=False)
    pode_transferir = Column(Boolean, default=False)
    pode_editar_equipamento = Column(Boolean, default=False)
    pode_abrir_chamado = Column(Boolean, default=True)
    pode_gerenciar_usuarios = Column(Boolean, default=False)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
