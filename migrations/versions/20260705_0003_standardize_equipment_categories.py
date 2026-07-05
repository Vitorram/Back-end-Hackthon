"""standardize equipment categories

Revision ID: 20260705_0003
Revises: 20260705_0002
Create Date: 2026-07-05 00:03:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260705_0003"
down_revision: Union[str, None] = "20260705_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE equipamentos
        SET tipo = CASE
            WHEN LOWER(tipo) IN ('desktop', 'pc', 'computador', 'computadores', 'monitor') THEN 'Computadores'
            WHEN LOWER(tipo) IN ('notebook', 'notebooks', 'laptop') THEN 'Notebooks'
            WHEN LOWER(tipo) IN ('tablet', 'tablets') THEN 'Tablets'
            WHEN LOWER(tipo) IN ('impressora', 'impressoras', 'printer') THEN 'Impressoras'
            WHEN LOWER(tipo) IN ('projetor', 'projetores', 'projector', 'datashow', 'data-show') THEN 'Projetores'
            WHEN LOWER(tipo) IN ('roteador', 'switch', 'access point', 'ap', 'wifi', 'rede', 'conectividade') THEN 'Dispositivos de conectividade'
            ELSE tipo
        END
    """)


def downgrade() -> None:
    pass