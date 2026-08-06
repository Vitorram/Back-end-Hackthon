"""add create equipment permission

Revision ID: 20260705_0002
Revises: 20260705_0001
Create Date: 2026-07-05 00:02:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260705_0002"
down_revision: Union[str, None] = "20260705_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _column_exists("usuarios", "pode_criar_equipamento"):
        op.add_column(
            "usuarios",
            sa.Column(
                "pode_criar_equipamento",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    op.execute(
        sa.text(
            "UPDATE usuarios "
            "SET pode_criar_equipamento = 1 "
            "WHERE pode_editar_equipamento = 1 OR perfil = 'SUPER_ADMIN'"
        )
    )


def downgrade() -> None:
    if _column_exists("usuarios", "pode_criar_equipamento"):
        op.drop_column("usuarios", "pode_criar_equipamento")