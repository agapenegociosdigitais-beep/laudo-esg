"""
Eureka Terra — ponto de entrada da API FastAPI.

Configura middlewares, rotas e lifecycle da aplicação.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import inicializar_banco, migrar_schema

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o lifecycle da aplicação:
    - Startup: inicializa banco de dados e cache
    - Shutdown: encerra conexões
    """
    logger.info("🌱 Iniciando Eureka Terra API...")

    # Cria tabelas no banco se não existirem
    try:
        await inicializar_banco()
        logger.info("✅ Banco de dados inicializado")

        # Migra schema (adiciona colunas novas sem derrubar tabelas)
        await migrar_schema()
        logger.info("✅ Schema migrado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")
        raise

    yield  # Aplicação em execução

    logger.info("🛑 Encerrando Eureka Terra API...")


# Instância principal da aplicação
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plataforma SaaS para análise ESG de propriedades rurais brasileiras",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middlewares ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rotas ─────────────────────────────────────────────────────────────────────

from app.api.endpoints import auth, propriedades, analises, relatorios, admin  # noqa: E402

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(propriedades.router, prefix="/api/v1/propriedades", tags=["Propriedades"])
app.include_router(analises.router, prefix="/api/v1/analises", tags=["Análises"])
app.include_router(relatorios.router, prefix="/api/v1/relatorios", tags=["Relatórios"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administração"])


# ── Endpoints utilitários ──────────────────────────────────────────────────────

@app.get("/", tags=["Status"])
async def raiz():
    """Endpoint raiz — verifica se a API está no ar."""
    return {"mensagem": "Eureka Terra API está funcionando 🌱", "versao": settings.APP_VERSION}


@app.get("/health", tags=["Status"])
async def health_check():
    """Health check para o Docker e load balancer."""
    return JSONResponse(content={"status": "ok", "ambiente": settings.ENVIRONMENT})
