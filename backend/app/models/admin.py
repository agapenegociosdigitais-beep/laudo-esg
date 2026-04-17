"""Modelos do painel administrativo."""
from uuid import UUID
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Date, Numeric, Text, ForeignKey,
    DateTime, Index, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


class AdminUser(Base):
    """Usuário administrador super-admin."""
    __tablename__ = "admin_users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="super_admin")
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacionamentos
    actions_log = relationship("AdminActionLog", back_populates="admin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_admin_users_email", "email"),
    )


class SearchLog(Base):
    """Log imutável de todas as pesquisas realizadas no sistema."""
    __tablename__ = "search_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True, index=True)
    car_code = Column(String(100), nullable=False, index=True)
    municipio = Column(String(255), nullable=True)
    area_hectares = Column(Numeric(12, 2), nullable=True)
    searched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Resultado PRODES
    has_prodes = Column(Boolean, nullable=False, default=False)
    prodes_area_ha = Column(Numeric(12, 2), nullable=True)
    prodes_percentage = Column(Numeric(5, 2), nullable=True)
    prodes_year = Column(Integer, nullable=True)

    # Resultado Embargo SEMA
    has_embargo_sema = Column(Boolean, nullable=False, default=False)
    embargo_type = Column(String(255), nullable=True)
    embargo_process_number = Column(String(100), nullable=True)
    embargo_date = Column(Date(), nullable=True)
    embargo_situation = Column(String(100), nullable=True)

    # Resultado Desmatamento
    has_deforestation = Column(Boolean, nullable=False, default=False)
    deforestation_area_ha = Column(Numeric(12, 2), nullable=True)
    deforestation_period = Column(String(100), nullable=True)
    deforestation_biome = Column(String(100), nullable=True)

    # Rastreamento
    analise_id = Column(PG_UUID(as_uuid=True), ForeignKey("analises.id", ondelete="SET NULL"), nullable=True)
    results_json = Column(JSONB, nullable=False, default=dict)

    # Relacionamentos
    cliente = relationship("Usuario")
    analise = relationship("Analise")

    __table_args__ = (
        Index("idx_search_logs_client", "client_id"),
        Index("idx_search_logs_car", "car_code"),
        Index("idx_search_logs_date", "searched_at"),
        Index("idx_search_logs_has_problems", "has_prodes", "has_embargo_sema", "has_deforestation"),
    )


class FlaggedCar(Base):
    """CARs marcados com um ou mais problemas (denormalizado para performance)."""
    __tablename__ = "flagged_cars"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    car_code = Column(String(100), nullable=False, unique=True, index=True)
    flag_type = Column(String(50), nullable=False, index=True)  # prodes|embargo_sema|deforestation|multiple
    severity = Column(String(20), nullable=True, index=True)  # critical|high|medium|low
    details_json = Column(JSONB, nullable=False, default=dict)
    first_detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Rastreamento
    search_log_id = Column(PG_UUID(as_uuid=True), ForeignKey("search_logs.id", ondelete="SET NULL"), nullable=True)
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True)

    # Relacionamentos
    search_log = relationship("SearchLog")
    cliente = relationship("Usuario")

    __table_args__ = (
        Index("idx_flagged_cars_type", "flag_type"),
        Index("idx_flagged_cars_severity", "severity"),
        Index("idx_flagged_cars_car", "car_code"),
    )


class AdminActionLog(Base):
    """Log imutável de todas as ações do administrador."""
    __tablename__ = "admin_actions_log"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    admin_id = Column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False, index=True)
    # approve_client|disapprove_client|suspend_client|edit_limit|reset_quota|login|logout|export_report
    target_type = Column(String(50), nullable=True)  # client|system|config
    target_id = Column(PG_UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relacionamentos
    admin = relationship("AdminUser", back_populates="actions_log")

    __table_args__ = (
        Index("idx_admin_actions_type", "action_type"),
        Index("idx_admin_actions_date", "created_at"),
    )


class AdminNotification(Base):
    """Notificações para o painel admin."""
    __tablename__ = "admin_notifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    type = Column(String(50), nullable=False)
    # new_client|prodes_alert|embargo_alert|deforest_alert|limit_warning|limit_reached
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    related_car = Column(String(100), nullable=True)
    related_client_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relacionamentos
    cliente = relationship("Usuario")

    __table_args__ = (
        Index("idx_notifications_read", "is_read"),
        Index("idx_notifications_created", "created_at"),
    )
