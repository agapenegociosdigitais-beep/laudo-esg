"""
Configuração do ambiente Alembic para migrations.

Lê a DATABASE_URL das configurações da aplicação (via pydantic-settings),
garantindo que as migrations sempre usem a mesma URL do ambiente.
Suporta tanto modo online (conexão real) quanto offline (geração de SQL).
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Importa o Base e os models para que o autogenerate detecte as tabelas
from app.core.database import Base
from app.core.config import get_settings

# Importa todos os models para registrá-los no metadata do Base
from app.models import usuario, propriedade, analise, relatorio  # noqa: F401

# Configuração de logging do Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata do SQLAlchemy — usado pelo autogenerate
target_metadata = Base.metadata

# Sobrescreve a URL do alembic.ini com a URL real do ambiente
settings = get_settings()
_db_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace(
    "postgresql+psycopg2://", "postgresql+asyncpg://"
)
config.set_main_option("sqlalchemy.url", _db_url)


def run_migrations_offline() -> None:
    """
    Modo offline: gera o SQL das migrations sem conectar ao banco.
    Útil para gerar scripts SQL para revisão manual.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Inclui tipos PostGIS nas migrations
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Executa as migrations numa conexão já estabelecida."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        # Compara tipos de colunas para detectar mudanças
        compare_type=True,
        # Compara valores padrão
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Modo online assíncrono: conecta ao banco e executa as migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Ponto de entrada para o modo online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
