from sqlalchemy import Column, Integer, String

from database.database import Base


class Escola(Base):
    __tablename__ = "escolas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    codigo = Column(String(30), unique=True, nullable=False)
    endereco = Column(String(255), nullable=True)
