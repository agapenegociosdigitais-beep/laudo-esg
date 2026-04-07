"""
Model de Propriedade Rural — armazena dados do CAR e geometria PostGIS.
"""
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Propriedade(Base):
    """
    Tabela de propriedades rurais cadastradas no SICAR.
    A geometria é armazenada em PostGIS (SRID 4326 = WGS84).
    """

    __tablename__ = "propriedades"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Número do CAR (ex: MT-5107248-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)
    numero_car: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # Localização
    estado: Mapped[str] = mapped_column(String(2), nullable=False, comment="UF do estado")
    municipio: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_propriedade: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Área em hectares (da declaração CAR)
    area_ha: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Geometria do polígono da propriedade (WGS84)
    geometria: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326),
        nullable=True,
    )

    # GeoJSON da geometria para cache/serialização rápida
    geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status no SICAR
    status_car: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Valores: ATIVO, PENDENTE, SUSPENSO, CANCELADO",
    )

    # Bioma principal da propriedade
    bioma: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Ex: Amazônia, Cerrado, Mata Atlântica, Caatinga, Pampa, Pantanal",
    )

    # Metadados adicionais do SICAR
    dados_sicar: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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
    analises: Mapped[list["Analise"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Analise", back_populates="propriedade", lazy="select"
    )
    relatorios: Mapped[list["Relatorio"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Relatorio", back_populates="propriedade", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Propriedade car={self.numero_car} municipio={self.municipio}>"
