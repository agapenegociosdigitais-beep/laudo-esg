"""
Model de Usuário — representa produtores rurais, traders e consultores
que acessam a plataforma Eureka Terra.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Usuario(Base):
    """Tabela de usuários da plataforma."""

    __tablename__ = "usuarios"

    # Chave primária UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Dados de autenticação
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Perfil
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    empresa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    perfil: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="consultor",
        comment="Valores: produtor, trader, consultor, admin",
    )

    # Status
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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

    # ── Controle de quota de consultas ───────────────────────────────────
    limite_consultas: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Limite de análises por mês (NULL = sem limite)"
    )
    consultas_mes_atual: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0",
        comment="Contador de análises no mês corrente"
    )
    mes_referencia: Mapped[str | None] = mapped_column(
        String(7), nullable=True, comment="Mês de referência do contador (YYYY-MM)"
    )

    # Relacionamentos
    relatorios: Mapped[list["Relatorio"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Relatorio", back_populates="usuario", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email}>"
