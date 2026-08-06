"""create saved reports

Revision ID: 20260705_0004
Revises: 20260705_0003
Create Date: 2026-07-05 00:04:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260705_0004"
down_revision: Union[str, None] = "20260705_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if _table_exists(table_name) and not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    if not _table_exists("relatorios_salvos"):
        op.create_table(
            "relatorios_salvos",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("titulo", sa.String(length=140), nullable=False),
            sa.Column("tipo", sa.String(length=60), nullable=False),
            sa.Column("parametros", sa.JSON(), nullable=False),
            sa.Column("resultado", sa.JSON(), nullable=False),
            sa.Column("criado_por_id", sa.Integer(), nullable=False),
            sa.Column("compartilhamento_token", sa.String(length=64), nullable=True),
            sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.Column("atualizado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["criado_por_id"], ["usuarios.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("compartilhamento_token"),
        )

    _create_index_if_missing("ix_relatorios_salvos_id", "relatorios_salvos", ["id"])
    _create_index_if_missing("ix_relatorios_salvos_tipo", "relatorios_salvos", ["tipo"])
    _create_index_if_missing("ix_relatorios_salvos_criado_por_id", "relatorios_salvos", ["criado_por_id"])
    _create_index_if_missing("ix_relatorios_salvos_compartilhamento_token", "relatorios_salvos", ["compartilhamento_token"], unique=True)


def downgrade() -> None:
    if _table_exists("relatorios_salvos"):
        op.drop_table("relatorios_salvos")
