"""Criação de tabelas para painel administrativo.

Adiciona suporte para:
- Autenticação super-admin
- Log de pesquisas (imutável)
- Rastreamento de CARs problemáticos
- Log de auditoria de ações admin
- Notificações do admin

Revision ID: 20260414_0003
Revises: 20240102_0001_002_embargos_areas_protegidas
Create Date: 2026-04-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260414_0003'
down_revision = None  # Esta é a primeira migration após o schema existente
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Estender tabela usuarios com campos de aprovação
    op.add_column('usuarios', sa.Column(
        'requerente_aprovacao',
        sa.Boolean(),
        nullable=False,
        server_default='true'
    ))
    op.add_column('usuarios', sa.Column(
        'approved_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))
    op.add_column('usuarios', sa.Column(
        'suspended_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))

    # 1. Tabela de usuários admin
    op.create_table(
        'admin_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='super_admin'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_admin_users_email')
    )
    op.create_index('idx_admin_users_email', 'admin_users', ['email'])

    # 2. Tabela de log de pesquisas
    op.create_table(
        'search_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('car_code', sa.String(100), nullable=False),
        sa.Column('municipio', sa.String(255), nullable=True),
        sa.Column('area_hectares', sa.Numeric(12, 2), nullable=True),
        sa.Column('searched_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('has_prodes', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('prodes_area_ha', sa.Numeric(12, 2), nullable=True),
        sa.Column('prodes_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('prodes_year', sa.Integer(), nullable=True),
        sa.Column('has_embargo_sema', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('embargo_type', sa.String(255), nullable=True),
        sa.Column('embargo_process_number', sa.String(100), nullable=True),
        sa.Column('embargo_date', sa.Date(), nullable=True),
        sa.Column('embargo_situation', sa.String(100), nullable=True),
        sa.Column('has_deforestation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deforestation_area_ha', sa.Numeric(12, 2), nullable=True),
        sa.Column('deforestation_period', sa.String(100), nullable=True),
        sa.Column('deforestation_biome', sa.String(100), nullable=True),
        sa.Column('analise_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('results_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['client_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['analise_id'], ['analises.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_search_logs_client', 'search_logs', ['client_id'])
    op.create_index('idx_search_logs_car', 'search_logs', ['car_code'])
    op.create_index('idx_search_logs_date', 'search_logs', ['searched_at'])
    op.create_index('idx_search_logs_has_problems', 'search_logs', ['has_prodes', 'has_embargo_sema', 'has_deforestation'])

    # 3. Tabela de CARs flaggeados
    op.create_table(
        'flagged_cars',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('car_code', sa.String(100), nullable=False, unique=True),
        sa.Column('flag_type', sa.String(50), nullable=False),  # prodes|embargo_sema|deforestation|multiple
        sa.Column('severity', sa.String(20), nullable=True),  # critical|high|medium|low
        sa.Column('details_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('first_detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('search_log_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['search_log_id'], ['search_logs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['client_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('car_code', name='uq_flagged_cars_car_code')
    )
    op.create_index('idx_flagged_cars_type', 'flagged_cars', ['flag_type'])
    op.create_index('idx_flagged_cars_severity', 'flagged_cars', ['severity'])
    op.create_index('idx_flagged_cars_car', 'flagged_cars', ['car_code'])

    # 4. Tabela de log de ações admin
    op.create_table(
        'admin_actions_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.String(100), nullable=False),  # approve_client|disapprove_client|etc
        sa.Column('target_type', sa.String(50), nullable=True),  # client|system|config
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_admin_actions_type', 'admin_actions_log', ['action_type'])
    op.create_index('idx_admin_actions_date', 'admin_actions_log', ['created_at'])

    # 5. Tabela de notificações
    op.create_table(
        'admin_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('type', sa.String(50), nullable=False),  # new_client|prodes_alert|embargo_alert|etc
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('related_car', sa.String(100), nullable=True),
        sa.Column('related_client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['related_client_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notifications_read', 'admin_notifications', ['is_read'])
    op.create_index('idx_notifications_created', 'admin_notifications', ['created_at'])

    # 6. Função PostgreSQL para resetar quotas mensais
    op.execute("""
        CREATE OR REPLACE FUNCTION reset_monthly_quota()
        RETURNS void AS $$
        BEGIN
          UPDATE usuarios
          SET consultas_mes_atual = 0,
              mes_referencia = TO_CHAR(NOW(), 'YYYY-MM')
          WHERE mes_referencia != TO_CHAR(NOW(), 'YYYY-MM');
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    # Remover função
    op.execute("DROP FUNCTION IF EXISTS reset_monthly_quota();")

    # Remover tabelas (na ordem inversa de dependências)
    op.drop_index('idx_notifications_created', table_name='admin_notifications')
    op.drop_index('idx_notifications_read', table_name='admin_notifications')
    op.drop_table('admin_notifications')

    op.drop_index('idx_admin_actions_date', table_name='admin_actions_log')
    op.drop_index('idx_admin_actions_type', table_name='admin_actions_log')
    op.drop_table('admin_actions_log')

    op.drop_index('idx_flagged_cars_car', table_name='flagged_cars')
    op.drop_index('idx_flagged_cars_severity', table_name='flagged_cars')
    op.drop_index('idx_flagged_cars_type', table_name='flagged_cars')
    op.drop_table('flagged_cars')

    op.drop_index('idx_search_logs_has_problems', table_name='search_logs')
    op.drop_index('idx_search_logs_date', table_name='search_logs')
    op.drop_index('idx_search_logs_car', table_name='search_logs')
    op.drop_index('idx_search_logs_client', table_name='search_logs')
    op.drop_table('search_logs')

    op.drop_index('idx_admin_users_email', table_name='admin_users')
    op.drop_table('admin_users')

    # Remover colunas de usuarios
    op.drop_column('usuarios', 'suspended_at')
    op.drop_column('usuarios', 'approved_at')
    op.drop_column('usuarios', 'requerente_aprovacao')
