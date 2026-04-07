"""
Model de Relatório PDF — registra os relatórios gerados para cada análise.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Relatorio(Base):
    """Registro de relatório PDF gerado para uma análise."""

    __tablename__ = "relatorios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Relacionamentos
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    propriedade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propriedades.id"), nullable=False, index=True
    )
    analise_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analises.id"), nullable=True
    )

    # Arquivo PDF
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho_arquivo: Mapped[str] = mapped_column(String(500), nullable=False)
    tamanho_bytes: Mapped[int | None] = mapped_column(nullable=True)

    # Status de geração
    status: Mapped[str] = mapped_column(
        String(20),
        default="gerando",
        nullable=False,
        comment="Valores: gerando, concluido, erro",
    )

    # Timestamps
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relacionamentos
    usuario: Mapped["Usuario"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Usuario", back_populates="relatorios"
    )
    propriedade: Mapped["Propriedade"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Propriedade", back_populates="relatorios"
    )
    analise: Mapped["Analise | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Analise", back_populates="relatorio"
    )

    def __repr__(self) -> str:
        return f"<Relatorio id={self.id} arquivo={self.nome_arquivo}>"
