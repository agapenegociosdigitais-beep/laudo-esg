#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Eureka Terra — Script de setup local (sem Docker)
# Configura o ambiente Python e Node para desenvolvimento direto na máquina.
# ─────────────────────────────────────────────────────────────────────────────
set -e

# Cores
VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
RESET='\033[0m'

info()    { echo -e "${VERDE}[INFO]${RESET} $1"; }
aviso()   { echo -e "${AMARELO}[AVISO]${RESET} $1"; }
erro()    { echo -e "${VERMELHO}[ERRO]${RESET} $1"; exit 1; }

echo ""
echo -e "${VERDE}🌱 Eureka Terra — Setup do ambiente local${RESET}"
echo "─────────────────────────────────────────"

# ─── Verificações de pré-requisitos ──────────────────────────────────────────

info "Verificando pré-requisitos..."

command -v python3 >/dev/null 2>&1 || erro "Python 3 não encontrado. Instale Python 3.11+."
command -v pip    >/dev/null 2>&1 || erro "pip não encontrado."
command -v node   >/dev/null 2>&1 || erro "Node.js não encontrado. Instale Node.js 20+."
command -v npm    >/dev/null 2>&1 || erro "npm não encontrado."

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python versão: $PYTHON_VERSION"

NODE_VERSION=$(node -v)
info "Node versão: $NODE_VERSION"

# ─── Arquivo .env ─────────────────────────────────────────────────────────────

if [ ! -f ".env" ]; then
    info "Criando .env a partir do .env.example..."
    cp .env.example .env
    aviso "Configure as credenciais no arquivo .env antes de executar a aplicação."
else
    info ".env já existe. Mantendo configurações atuais."
fi

# ─── Backend Python ───────────────────────────────────────────────────────────

info "Configurando ambiente Python (backend)..."

cd backend

# Cria virtualenv se não existir
if [ ! -d ".venv" ]; then
    info "Criando virtualenv em backend/.venv..."
    python3 -m venv .venv
fi

# Ativa o virtualenv
# shellcheck disable=SC1091
source .venv/bin/activate

info "Instalando dependências Python..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

info "Verificando instalação do FastAPI..."
python3 -c "import fastapi; print(f'  FastAPI {fastapi.__version__} ✅')"
python3 -c "import sqlalchemy; print(f'  SQLAlchemy {sqlalchemy.__version__} ✅')"
python3 -c "import geopandas; print(f'  GeoPandas {geopandas.__version__} ✅')" 2>/dev/null \
    || aviso "GeoPandas não instalado — requer GDAL no sistema."

deactivate
cd ..

# ─── Frontend Node ────────────────────────────────────────────────────────────

info "Configurando frontend Next.js..."
cd frontend

info "Instalando dependências npm..."
npm install --legacy-peer-deps --silent

info "Verificando TypeScript..."
npx tsc --noEmit 2>/dev/null && echo "  TypeScript ✅" || aviso "Erros de tipo encontrados — execute 'npm run type-check' para detalhes."

cd ..

# ─── Alembic ─────────────────────────────────────────────────────────────────

info "Verificando configuração do Alembic..."
if [ -f "backend/alembic.ini" ]; then
    echo "  Alembic configurado ✅"
else
    aviso "alembic.ini não encontrado. Execute 'make migrate' após subir o banco."
fi

# ─── Resumo ──────────────────────────────────────────────────────────────────

echo ""
echo -e "${VERDE}─────────────────────────────────────────${RESET}"
echo -e "${VERDE}✅ Setup concluído!${RESET}"
echo ""
echo "Próximos passos:"
echo ""
echo "  # Opção 1 — Com Docker (recomendado)"
echo "  make up"
echo "  make migrate"
echo ""
echo "  # Opção 2 — Sem Docker (requer PostgreSQL/Redis locais)"
echo "  cd backend && source .venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "  # Em outro terminal:"
echo "  cd frontend && npm run dev"
echo ""
echo "  Acesse: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
