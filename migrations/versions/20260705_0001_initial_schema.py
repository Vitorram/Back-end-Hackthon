"""initial schema

Revision ID: 20260705_0001
Revises:
Create Date: 2026-07-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260705_0001"
down_revision: Union[str, None] = None
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
    if not _table_exists("escolas"):
        op.create_table(
            "escolas",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=120), nullable=False),
            sa.Column("codigo", sa.String(length=30), nullable=False),
            sa.Column("endereco", sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("codigo"),
        )
    _create_index_if_missing("ix_escolas_id", "escolas", ["id"])

    if not _table_exists("usuarios"):
        op.create_table(
            "usuarios",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=120), nullable=False),
            sa.Column("matricula", sa.String(length=30), nullable=True),
            sa.Column("email", sa.String(length=120), nullable=False),
            sa.Column("senha_hash", sa.String(length=255), nullable=False),
            sa.Column("perfil", sa.Enum("COMMON", "MANAGER", "SUPER_ADMIN"), nullable=False),
            sa.Column("escola_id", sa.Integer(), nullable=True),
            sa.Column("ativo", sa.Boolean(), nullable=True),
            sa.Column("aprovado", sa.Boolean(), nullable=True),
            sa.Column("aprovado_por", sa.Integer(), nullable=True),
            sa.Column("aprovado_em", sa.DateTime(), nullable=True),
            sa.Column("ultimo_acesso", sa.DateTime(), nullable=True),
            sa.Column("pode_ver_dashboard", sa.Boolean(), nullable=True),
            sa.Column("pode_transferir", sa.Boolean(), nullable=True),
            sa.Column("pode_editar_equipamento", sa.Boolean(), nullable=True),
            sa.Column("pode_abrir_chamado", sa.Boolean(), nullable=True),
            sa.Column("pode_gerenciar_usuarios", sa.Boolean(), nullable=True),
            sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.Column("atualizado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["aprovado_por"], ["usuarios.id"]),
            sa.ForeignKeyConstraint(["escola_id"], ["escolas.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("matricula"),
        )
    _create_index_if_missing("ix_usuarios_id", "usuarios", ["id"])

    if not _table_exists("equipamentos"):
        op.create_table(
            "equipamentos",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("patrimonio", sa.String(length=50), nullable=True),
            sa.Column("codigo_interno", sa.String(length=50), nullable=False),
            sa.Column("tipo", sa.String(length=80), nullable=False),
            sa.Column("marca", sa.String(length=80), nullable=True),
            sa.Column("modelo", sa.String(length=100), nullable=True),
            sa.Column("numero_serie", sa.String(length=100), nullable=True),
            sa.Column("data_aquisicao", sa.Date(), nullable=True),
            sa.Column(
                "status",
                sa.Enum(
                    "EM_USO",
                    "EM_MANUTENCAO",
                    "DEFEITUOSO",
                    "DESCARTADO",
                    "DISPONIVEL",
                    "INOPERANTE",
                    "EM_TRANSFERENCIA",
                ),
                nullable=True,
            ),
            sa.Column("escola_atual_id", sa.Integer(), nullable=False),
            sa.Column("sala_atual", sa.String(length=100), nullable=True),
            sa.Column("url_foto", sa.String(length=255), nullable=True),
            sa.Column("observacoes", sa.Text(), nullable=True),
            sa.Column("adquirido_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.Column("atualizado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["escola_atual_id"], ["escolas.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_equipamentos_codigo_interno", "equipamentos", ["codigo_interno"], unique=True)
    _create_index_if_missing("ix_equipamentos_escola_atual_id", "equipamentos", ["escola_atual_id"])
    _create_index_if_missing("ix_equipamentos_id", "equipamentos", ["id"])
    _create_index_if_missing("ix_equipamentos_patrimonio", "equipamentos", ["patrimonio"], unique=True)

    if not _table_exists("historico_equipamentos"):
        op.create_table(
            "historico_equipamentos",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("equipamento_id", sa.Integer(), nullable=False),
            sa.Column("usuario_id", sa.Integer(), nullable=True),
            sa.Column(
                "tipo_evento",
                sa.Enum(
                    "CRIADO",
                    "ATUALIZADO",
                    "TRANSFERIDO",
                    "CHAMADO_ABERTO",
                    "MANUTENCAO_INICIADA",
                    "MANUTENCAO_FINALIZADA",
                    "DESCARTADO",
                ),
                nullable=False,
            ),
            sa.Column("descricao", sa.Text(), nullable=True),
            sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["equipamento_id"], ["equipamentos.id"]),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_historico_equipamentos_id", "historico_equipamentos", ["id"])

    if not _table_exists("movimentacoes"):
        op.create_table(
            "movimentacoes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("equipamento_id", sa.Integer(), nullable=False),
            sa.Column("escola_origem_id", sa.Integer(), nullable=True),
            sa.Column("escola_destino_id", sa.Integer(), nullable=False),
            sa.Column("motivo", sa.String(length=255), nullable=True),
            sa.Column("usuario_responsavel_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=True),
            sa.Column("movimentado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["equipamento_id"], ["equipamentos.id"]),
            sa.ForeignKeyConstraint(["escola_destino_id"], ["escolas.id"]),
            sa.ForeignKeyConstraint(["escola_origem_id"], ["escolas.id"]),
            sa.ForeignKeyConstraint(["usuario_responsavel_id"], ["usuarios.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_movimentacoes_id", "movimentacoes", ["id"])

    if not _table_exists("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("usuario_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    _create_index_if_missing("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    _create_index_if_missing("ix_refresh_tokens_usuario_id", "refresh_tokens", ["usuario_id"])


def downgrade() -> None:
    if _table_exists("refresh_tokens"):
        op.drop_table("refresh_tokens")
    if _table_exists("movimentacoes"):
        op.drop_table("movimentacoes")
    if _table_exists("historico_equipamentos"):
        op.drop_table("historico_equipamentos")
    if _table_exists("equipamentos"):
        op.drop_table("equipamentos")
    if _table_exists("usuarios"):
        op.drop_table("usuarios")
    if _table_exists("escolas"):
        op.drop_table("escolas")
