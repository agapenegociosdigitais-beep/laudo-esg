"""
Configura��o do banco de dados PostgreSQL/PostGIS com SQLAlchemy ass�ncrono.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Converte a URL do PostgreSQL para o driver asyncpg
_db_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace(
    "postgresql+psycopg2://", "postgresql+asyncpg://"
)

# Motor ass�ncrono com pool de conex�es
engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,   # Verifica conex�o antes de usar
    pool_size=10,
    max_overflow=20,
)

# F�brica de sess�es ass�ncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Classe base para todos os models SQLAlchemy."""
    pass


async def get_db():  # type: ignore[override]
    """Depend�ncia FastAPI que fornece sess�o de banco de dados."""
    async with AsyncSessionLocal() as sessao:
        try:
            yield sessao
            await sessao.commit()
        except Exception:
            await sessao.rollback()
            raise
        finally:
            await sessao.close()


async def inicializar_banco() -> None:
    """Cria todas as tabelas no banco de dados na inicializa��o."""
    # Importa models para registr�-los no metadata do Base
    from app.models import usuario, propriedade, analise, relatorio  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def migrar_schema() -> None:
    """Adiciona colunas novas sem derrubar tabelas existentes (create_all n�o faz isso)."""
    queries = [
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS limite_consultas INTEGER",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS consultas_mes_atual INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS mes_referencia VARCHAR(7)",
    ]
    async with engine.begin() as conn:
        for q in queries:
            await conn.execute(text(q))
