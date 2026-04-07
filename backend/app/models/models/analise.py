"""
Model de Análise — armazena resultados de conformidade ESG, embargos,
áreas protegidas, desmatamento e Moratória/EUDR para uma propriedade.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Analise(Base):
    """
    Resultado de análise geoespacial de uma propriedade.
    Cada registro representa uma análise em um período específico.
    """

    __tablename__ = "analises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Propriedade analisada
    propriedade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propriedades.id"), nullable=False, index=True
    )

    # Período da análise
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False)

    # ── Embargos Ambientais ───────────────────────────────────────────────────
    # Cada campo armazena o dict retornado por ResultadoEmbargo.para_dict()
    # Campos: embargado (bool|None), orgao, numero_embargo, data_embargo,
    #         area_embargada_ha, motivo, fonte, verificado, status_display
    embargo_ibama: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Resultado da verificação de embargo no IBAMA/CTF",
    )
    embargo_semas: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Resultado da verificação de embargo na SEMAS-PA/SIMLAM",
    )

    # ── Áreas Protegidas ──────────────────────────────────────────────────────
    # Cada campo armazena o dict retornado por ResultadoAreaProtegida.para_dict()
    # Campos: sobreposicao_detectada (bool|None), tipo_verificacao, nome_area,
    #         categoria, percentual_sobreposicao, area_sobreposicao_ha, esfera,
    #         fonte, verificado, status_display
    sobreposicao_uc: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Sobreposição com Unidades de Conservação (CNUC/MMA)",
    )
    sobreposicao_ti: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Sobreposição com Terras Indígenas (FUNAI)",
    )

    # ── Cobertura e Uso do Solo (MapBiomas) ───────────────────────────────────
    cobertura_solo: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="% de cada classe de cobertura (floresta, pastagem, soja, etc.)",
    )

    # ── Desmatamento (PRODES/INPE) ────────────────────────────────────────────
    area_desmatada_ha: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Área total desmatada no período (ha)"
    )
    desmatamento_detectado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dados_desmatamento: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Conformidade — Moratória da Soja ─────────────────────────────────────
    moratorio_soja_conforme: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    moratorio_soja_detalhe: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Conformidade — EUDR (EU Deforestation Regulation) ────────────────────
    eudr_conforme: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    eudr_detalhe: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Conformidade Socioambiental (quilombola, assentamento, trabalho, RL/APP) ─
    resultado_conformidade: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment=(
            "Dados de conformidade socioambiental: quilombola, assentamento, "
            "trabalho_escravo, balanco_ambiental (RL/APP), marco_ue, bioma, estado"
        ),
    )

    # ── Score ESG Geral ───────────────────────────────────────────────────────
    # Regras: embargo IBAMA/SEMAS/TI → 0 (CRÍTICO)
    #         sobreposição UC → -40 pts
    #         sem irregularidade → 100 (BAIXO)
    score_esg: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Score de 0 a 100"
    )
    nivel_risco: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Valores: BAIXO, MÉDIO, ALTO, CRÍTICO",
    )

    # Status do processamento
    status: Mapped[str] = mapped_column(
        String(20),
        default="pendente",
        nullable=False,
        comment="Valores: pendente, processando, concluido, erro",
    )
    erro_mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    propriedade: Mapped["Propriedade"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Propriedade", back_populates="analises"
    )
    relatorio: Mapped["Relatorio | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Relatorio", back_populates="analise", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Analise id={self.id} score_esg={self.score_esg} nivel={self.nivel_risco}>"
