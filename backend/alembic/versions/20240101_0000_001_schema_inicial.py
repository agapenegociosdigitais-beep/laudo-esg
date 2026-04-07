"""Schema inicial — usuarios, propriedades, analises, relatorios

Revision ID: 001_schema_inicial
Reverts:     None
Created:     2024-01-01
"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_schema_inicial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria todas as tabelas do schema inicial."""

    # ── Extensões PostGIS ────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── Tabela: usuarios ─────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("empresa", sa.String(255), nullable=True),
        sa.Column("perfil", sa.String(50), nullable=False, server_default="consultor"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    # ── Tabela: propriedades ─────────────────────────────────────────────────
    op.create_table(
        "propriedades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("numero_car", sa.String(100), nullable=False, unique=True),
        sa.Column("estado", sa.String(2), nullable=False),
        sa.Column("municipio", sa.String(255), nullable=False),
        sa.Column("nome_propriedade", sa.String(500), nullable=True),
        sa.Column("area_ha", sa.Float(), nullable=True),
        sa.Column(
            "geometria",
            geoalchemy2.types.Geometry(geometry_type="MULTIPOLYGON", srid=4326),
            nullable=True,
        ),
        sa.Column("geojson", postgresql.JSONB(), nullable=True),
        sa.Column("status_car", sa.String(50), nullable=True),
        sa.Column("bioma", sa.String(100), nullable=True),
        sa.Column("dados_sicar", postgresql.JSONB(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_propriedades_numero_car", "propriedades", ["numero_car"], unique=True)

    # ── Tabela: analises ─────────────────────────────────────────────────────
    op.create_table(
        "analises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("propriedade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("propriedades.id"), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=False),
        # NDVI
        sa.Column("ndvi_medio", sa.Float(), nullable=True),
        sa.Column("ndvi_minimo", sa.Float(), nullable=True),
        sa.Column("ndvi_maximo", sa.Float(), nullable=True),
        sa.Column("ndvi_desvio_padrao", sa.Float(), nullable=True),
        sa.Column("ndvi_serie_temporal", postgresql.JSONB(), nullable=True),
        sa.Column("fonte_ndvi", sa.String(100), nullable=True),
        # Cobertura do solo
        sa.Column("cobertura_solo", postgresql.JSONB(), nullable=True),
        # Desmatamento
        sa.Column("area_desmatada_ha", sa.Float(), nullable=True),
        sa.Column("desmatamento_detectado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dados_desmatamento", postgresql.JSONB(), nullable=True),
        # Conformidade
        sa.Column("moratorio_soja_conforme", sa.Boolean(), nullable=True),
        sa.Column("moratorio_soja_detalhe", sa.Text(), nullable=True),
        sa.Column("eudr_conforme", sa.Boolean(), nullable=True),
        sa.Column("eudr_detalhe", sa.Text(), nullable=True),
        # Score ESG
        sa.Column("score_esg", sa.Float(), nullable=True),
        sa.Column("nivel_risco", sa.String(20), nullable=True),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="pendente"),
        sa.Column("erro_mensagem", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_analises_propriedade_id", "analises", ["propriedade_id"])

    # ── Tabela: relatorios ───────────────────────────────────────────────────
    op.create_table(
        "relatorios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("propriedade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("propriedades.id"), nullable=False),
        sa.Column("analise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analises.id"), nullable=True),
        sa.Column("nome_arquivo", sa.String(255), nullable=False),
        sa.Column("caminho_arquivo", sa.String(500), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="gerando"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_relatorios_usuario_id", "relatorios", ["usuario_id"])
    op.create_index("ix_relatorios_propriedade_id", "relatorios", ["propriedade_id"])


def downgrade() -> None:
    """Remove todas as tabelas do schema inicial."""
    op.drop_table("relatorios")
    op.drop_table("analises")
    op.drop_table("propriedades")
    op.drop_table("usuarios")
