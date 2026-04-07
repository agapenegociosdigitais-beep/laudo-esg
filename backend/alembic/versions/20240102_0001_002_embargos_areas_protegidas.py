"""Adiciona campos de embargos e áreas protegidas; remove campos NDVI

Revision ID: 002_embargos_areas_protegidas
Reverts:     001_schema_inicial
Created:     2024-01-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_embargos_areas_protegidas"
down_revision: Union[str, None] = "001_schema_inicial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migra a tabela analises para o novo modelo de conformidade ESG.

    Remoções: campos NDVI que dependiam do Copernicus/Sentinel-2.
    Adições:  4 campos JSONB para embargos IBAMA/SEMAS e sobreposição UC/TI.
    """

    # ── Remove colunas NDVI (Copernicus/Sentinel-2 removido do projeto) ───────
    op.drop_column("analises", "ndvi_medio")
    op.drop_column("analises", "ndvi_minimo")
    op.drop_column("analises", "ndvi_maximo")
    op.drop_column("analises", "ndvi_desvio_padrao")
    op.drop_column("analises", "ndvi_serie_temporal")
    op.drop_column("analises", "fonte_ndvi")

    # ── Adiciona colunas de embargo IBAMA ─────────────────────────────────────
    # Armazena o dict ResultadoEmbargo.para_dict():
    #   {embargado, orgao, numero_embargo, data_embargo, area_embargada_ha,
    #    motivo, fonte, verificado, status_display}
    op.add_column(
        "analises",
        sa.Column(
            "embargo_ibama",
            postgresql.JSONB(),
            nullable=True,
            comment="Resultado da verificação de embargo no IBAMA/CTF",
        ),
    )

    # ── Adiciona colunas de embargo SEMAS-PA ──────────────────────────────────
    op.add_column(
        "analises",
        sa.Column(
            "embargo_semas",
            postgresql.JSONB(),
            nullable=True,
            comment="Resultado da verificação de embargo na SEMAS-PA/SIMLAM",
        ),
    )

    # ── Adiciona coluna de sobreposição com Unidades de Conservação ───────────
    # Armazena o dict ResultadoAreaProtegida.para_dict():
    #   {sobreposicao_detectada, tipo_verificacao, nome_area, categoria,
    #    percentual_sobreposicao, area_sobreposicao_ha, esfera, fonte,
    #    verificado, status_display}
    op.add_column(
        "analises",
        sa.Column(
            "sobreposicao_uc",
            postgresql.JSONB(),
            nullable=True,
            comment="Sobreposição com Unidades de Conservação (CNUC/MMA)",
        ),
    )

    # ── Adiciona coluna de sobreposição com Terras Indígenas ──────────────────
    op.add_column(
        "analises",
        sa.Column(
            "sobreposicao_ti",
            postgresql.JSONB(),
            nullable=True,
            comment="Sobreposição com Terras Indígenas (FUNAI)",
        ),
    )


def downgrade() -> None:
    """Reverte para o schema anterior: remove novos campos e restaura NDVI."""

    # Remove as novas colunas de embargos e áreas protegidas
    op.drop_column("analises", "sobreposicao_ti")
    op.drop_column("analises", "sobreposicao_uc")
    op.drop_column("analises", "embargo_semas")
    op.drop_column("analises", "embargo_ibama")

    # Restaura as colunas NDVI removidas
    op.add_column("analises", sa.Column("fonte_ndvi", sa.String(100), nullable=True))
    op.add_column("analises", sa.Column("ndvi_serie_temporal", postgresql.JSONB(), nullable=True))
    op.add_column("analises", sa.Column("ndvi_desvio_padrao", sa.Float(), nullable=True))
    op.add_column("analises", sa.Column("ndvi_maximo", sa.Float(), nullable=True))
    op.add_column("analises", sa.Column("ndvi_minimo", sa.Float(), nullable=True))
    op.add_column("analises", sa.Column("ndvi_medio", sa.Float(), nullable=True))
