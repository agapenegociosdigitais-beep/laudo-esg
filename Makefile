## ─────────────────────────────────────────────────────────────────────────────
## Eureka Terra — Makefile
## Uso: make <comando>
## ─────────────────────────────────────────────────────────────────────────────

.PHONY: help up down build logs ps \
        migrate migrate-create migrate-history \
        backend-shell backend-test \
        frontend-install frontend-dev \
        setup clean

# Cores para output legível
VERDE  := \033[0;32m
RESET  := \033[0m
NEGRITO := \033[1m

help: ## Exibe esta ajuda
	@echo ""
	@echo "$(NEGRITO)🌱 Eureka Terra — Comandos disponíveis$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(VERDE)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ─── Docker Compose ───────────────────────────────────────────────────────────

up: ## Sobe todos os containers (build se necessário)
	docker compose up --build -d
	@echo "$(VERDE)✅ Plataforma rodando em http://localhost:3000$(RESET)"
	@echo "   API Swagger: http://localhost:8000/docs"

down: ## Para e remove os containers
	docker compose down

build: ## Rebuild completo de todos os containers
	docker compose build --no-cache

logs: ## Exibe logs em tempo real (todos os serviços)
	docker compose logs -f

logs-backend: ## Logs apenas do backend
	docker compose logs -f backend

logs-frontend: ## Logs apenas do frontend
	docker compose logs -f frontend

ps: ## Lista containers em execução
	docker compose ps

restart-backend: ## Reinicia apenas o backend
	docker compose restart backend

# ─── Migrations (Alembic) ─────────────────────────────────────────────────────

migrate: ## Aplica todas as migrations pendentes
	docker compose exec backend alembic upgrade head
	@echo "$(VERDE)✅ Migrations aplicadas$(RESET)"

migrate-create: ## Cria nova migration (uso: make migrate-create MSG="descricao")
	@[ -n "$(MSG)" ] || (echo "❌ Informe a mensagem: make migrate-create MSG='sua descricao'"; exit 1)
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## Exibe histórico de migrations
	docker compose exec backend alembic history --verbose

migrate-down: ## Reverte a última migration
	docker compose exec backend alembic downgrade -1

migrate-reset: ## Reverte TODAS as migrations (⚠ apaga dados)
	@echo "⚠️  Isso apagará todos os dados do banco. Pressione CTRL+C para cancelar..."
	@sleep 3
	docker compose exec backend alembic downgrade base

# ─── Backend ──────────────────────────────────────────────────────────────────

backend-shell: ## Abre shell no container do backend
	docker compose exec backend bash

backend-test: ## Executa testes do backend
	docker compose exec backend pytest tests/ -v

# ─── Frontend ─────────────────────────────────────────────────────────────────

frontend-install: ## Instala dependências do frontend (local)
	cd frontend && npm install --legacy-peer-deps

frontend-dev: ## Inicia frontend em modo dev (local, sem Docker)
	cd frontend && npm run dev

frontend-build: ## Build de produção do frontend (local)
	cd frontend && npm run build

frontend-type-check: ## Verifica tipos TypeScript
	cd frontend && npm run type-check

# ─── Setup local (sem Docker) ─────────────────────────────────────────────────

setup: ## Configura ambiente local completo (Python + Node)
	@bash scripts/setup.sh

# ─── Utilitários ──────────────────────────────────────────────────────────────

env: ## Copia .env.example para .env (se não existir)
	@[ -f .env ] && echo "⚠️  .env já existe. Não sobrescrito." || (cp .env.example .env && echo "$(VERDE)✅ .env criado a partir do .env.example$(RESET)")

clean: ## Remove containers, volumes e arquivos gerados
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	cd frontend && rm -rf .next node_modules 2>/dev/null || true
	@echo "$(VERDE)✅ Limpeza concluída$(RESET)"

status: ## Verifica saúde da API e banco
	@echo "--- Backend ---"
	@curl -sf http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend não acessível"
	@echo "--- Frontend ---"
	@curl -sf -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3000 || echo "❌ Frontend não acessível"
