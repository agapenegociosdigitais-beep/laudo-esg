"""
Configurao do banco de dados PostgreSQL/PostGIS com SQLAlchemy assncrono.
"""
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

# Motor assncrono com pool de conexes
engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,   # Verifica conexo antes de usar
    pool_size=10,
    max_overflow=20,
)

# Fbrica de sesses assncronas
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
    """Dependncia FastAPI que fornece sesso de banco de dados."""
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
    """Cria todas as tabelas no banco de dados na inicializao."""
    # Importa models para registr-los no metadata do Base
    from app.models import usuario, propriedade, analise, relatorio  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
