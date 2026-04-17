# ✅ CHECKLIST DE IMPLEMENTAÇÃO — Painel Admin GeoRural

## FASE 1: BANCO DE DADOS ✅ COMPLETO

- [x] Criar tabela `admin_users`
- [x] Criar tabela `search_logs` com 18 campos
- [x] Criar tabela `flagged_cars`
- [x] Criar tabela `admin_actions_log`
- [x] Criar tabela `admin_notifications`
- [x] Adicionar colunas em `usuarios` (requerente_aprovacao, approved_at, suspended_at)
- [x] Criar índices otimizados (11 índices)
- [x] Criar função `reset_monthly_quota()`
- [x] Escrever migration SQL (alembic)

**Arquivos:** `backend/alembic/versions/20260414_0003_admin_panel_tables.py`

---

## FASE 2: BACKEND ✅ COMPLETO

### 2.1 Modelos
- [x] `AdminUser`
- [x] `SearchLog`
- [x] `FlaggedCar`
- [x] `AdminActionLog`
- [x] `AdminNotification`

**Arquivo:** `backend/app/models/admin.py`

### 2.2 Autenticação
- [x] `AdminJWT` class
- [x] `criar_token()` method
- [x] `validar_token()` method
- [x] `obter_admin_atual()` dependency
- [x] HTTPBearer security scheme
- [x] Config com ADMIN_EMAIL, ADMIN_PASSWORD

**Arquivo:** `backend/app/core/admin_security.py`

### 2.3 Lógica de Negócio (Service Layer)
- [x] `registrar_login()`
- [x] `registrar_acao()`
- [x] `listar_clientes_paginado()`
- [x] `get_cliente_perfil()`
- [x] `aprovar_cliente()`
- [x] `desaprovar_cliente()`
- [x] `suspender_cliente()`
- [x] `editar_limite()`
- [x] `get_overview_metricas()`
- [x] `get_pesquisas_por_dia()`
- [x] `get_cars_por_status()`
- [x] `get_top_clientes()`
- [x] `get_dashboard_graficos()`
- [x] `criar_notificacao()`
- [x] `listar_notificacoes()`
- [x] `contar_notificacoes_nao_lidas()`
- [x] `marcar_notificacao_lida()`

**Arquivo:** `backend/app/services/admin_service.py`

### 2.4 Endpoints (22 rotas)
- [x] POST `/admin/login`
- [x] POST `/admin/logout`
- [x] GET `/admin/me`
- [x] GET `/admin/metrics/overview`
- [x] GET `/admin/metrics/graficos`
- [x] GET `/admin/clientes`
- [x] GET `/admin/clientes/{id}`
- [x] PATCH `/admin/clientes/{id}/aprovar`
- [x] PATCH `/admin/clientes/{id}/desaprovar`
- [x] PATCH `/admin/clientes/{id}/suspender`
- [x] PATCH `/admin/clientes/{id}/limite`
- [x] GET `/admin/notificacoes`
- [x] GET `/admin/notificacoes/unread-count`
- [x] PATCH `/admin/notificacoes/{id}/ler`
- [x] GET `/admin/logs`
- [x] PATCH `/admin/config/password`
- [x] GET `/admin/config/info`

**Arquivo:** `backend/app/api/endpoints/admin_new.py`

### 2.5 Schemas
- [x] `AdminLoginRequest`
- [x] `AdminTokenResposta`
- [x] `AdminResposta`
- [x] `ClientePerfil`
- [x] `ClienteListaItem`
- [x] `AprovarClienteRequest`
- [x] `EditarLimiteRequest`
- [x] `SearchLogResposta`
- [x] `NotificacaoResposta`
- [x] `AdminActionResposta`
- [x] `OverviewMetricas`
- [x] `PesquisasPorDia`, `CARsPorStatus`, `TopCliente`
- [x] `DashboardGraficos`

**Arquivo:** `backend/app/schemas/admin.py` (expanded)

### 2.6 Configuração
- [x] Adicionar `ADMIN_EMAIL` em `.env`
- [x] Adicionar `ADMIN_PASSWORD` em `.env`
- [x] Adicionar `ADMIN_PASSWORD_HASH` property em `config.py`
- [x] Registrar router em `main.py`

**Arquivos:** `.env`, `backend/app/core/config.py`, `backend/app/main.py`

---

## FASE 3: FRONTEND ⏳ TODO (20h)

### 3.1 Setup & Autenticação (3h)
- [ ] Criar `contexts/AdminAuthContext.tsx`
- [ ] Criar `services/adminService.ts`
- [ ] Criar `types/admin.ts`
- [ ] Criar `hooks/useAdminAuth.ts`
- [ ] Criar `middleware.ts` (proteção de rotas)
- [ ] Criar página `/admin/login`

### 3.2 Layout Base (2h)
- [ ] Criar `app/admin/layout.tsx` (RootLayout)
- [ ] Criar `components/AdminSidebar` (menu 9 items)
- [ ] Criar `components/AdminHeader` (logo + greeting + bells + logout)
- [ ] Criar `app/admin/page.tsx` (redirect to dashboard)

### 3.3 Dashboard (3h)
- [ ] Criar `app/admin/dashboard/page.tsx`
- [ ] Implementar 4 metric cards
- [ ] Integrar Recharts LineChart (pesquisas/dia)
- [ ] Integrar Recharts PieChart (CARs status)
- [ ] Integrar Recharts BarChart (top clientes)
- [ ] Adicionar loading states

### 3.4 Gestão de Clientes (4h)
- [ ] Criar `app/admin/clientes/page.tsx`
- [ ] Tabela com 20 clientes
- [ ] Filtro por status
- [ ] Campo de busca (nome/email)
- [ ] Botões inline (Aprovar/Desaprovar/Suspender/Editar)
- [ ] Modal para editar limite
- [ ] Paginação
- [ ] Criar `app/admin/clientes/[id]/page.tsx` (perfil detalhado)

### 3.5 Log de Pesquisas (3h)
- [ ] Criar `app/admin/pesquisas/page.tsx`
- [ ] Tabela com CAR, Cliente, Data, Resultado
- [ ] Filtro por data (de/até)
- [ ] Filtro por cliente (dropdown)
- [ ] Filtro por resultado (Limpo/PRODES/Embargo/Desm)
- [ ] Busca por código CAR
- [ ] Badge colorido para cada resultado
- [ ] Paginação
- [ ] Botão Exportar

### 3.6 CARs Problemáticos (3h)
- [ ] Criar `app/admin/cars-problematicos/page.tsx`
- [ ] **Aba 1: PRODES** (CAR, Municipio, Área Total, Área PRODES, %, Ano, Severidade)
- [ ] **Aba 2: Embargo** (CAR, Tipo, Processo, Data, Situação)
- [ ] **Aba 3: Desmatamento** (CAR, Área, Período, Bioma)
- [ ] **Aba 4: Consolidado** (Cards + CARs múltiplos problemas + Gráfico temporal)
- [ ] Sistema de abas (Tabs)
- [ ] Paginação em cada aba

### 3.7 Notificações (2h)
- [ ] Criar `app/admin/notificacoes/page.tsx`
- [ ] Criar `components/NotificationBell`
- [ ] Sino com badge contador
- [ ] Dropdown com últimas 5 notif
- [ ] Link "Ver todas" → página completa
- [ ] Polling 30s para atualizar
- [ ] Marca como lida

### 3.8 Auditoria & Configurações (2h)
- [ ] Criar `app/admin/auditoria/page.tsx`
- [ ] Log filtrado por tipo de ação + datas
- [ ] Criar `app/admin/configuracoes/page.tsx`
- [ ] Formulário alterar senha (validação 8 chars)
- [ ] Campo email para alertas

### 3.9 Exportação (2h)
- [ ] Criar `app/admin/relatorios/page.tsx`
- [ ] PDF: jsPDF + autoTable (header + tabelas + gráficos)
- [ ] Excel: xlsx (múltiplas sheets)
- [ ] Exportar de qualquer tabela (pesquisas, clientes, CARs)
- [ ] Formatação profissional (cores, bold)

### 3.10 Componentes Reutilizáveis (3h)
- [ ] `components/MetricCard` (ícone + valor + tendência)
- [ ] `components/ClientTable` (tabela genérica paginada)
- [ ] `components/ClientModal` (modal de ações)
- [ ] `components/SearchTable` (tabela de pesquisas)
- [ ] `components/CARTable` (tabela de CARs problemáticos)
- [ ] `components/LoadingSkeleton` (state de carregamento)
- [ ] `components/ErrorAlert` (tratamento de erro)
- [ ] `components/ConfirmDialog` (confirmação de ações)

---

## FASE 4: INTEGRAÇÕES & POLISH (2h)

- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Dark mode CSS variables
- [ ] Sistema de Toast (sonner ou react-hot-toast)
- [ ] Loading states em todas as requisições
- [ ] Error boundaries
- [ ] SWR/TanStack Query para cache
- [ ] Validação de formulários
- [ ] Confirmar antes de ações destrutivas

---

## FASE 5: TESTES E2E (2h)

- [ ] Testar login com `admin@georural.com` / `Admin@123456`
- [ ] Testar dashboard carrega e populam cards
- [ ] Testar listagem de clientes (aprovar, desaprovar, editar limite)
- [ ] Testar filtros em clientes
- [ ] Testar tabela de pesquisas e filtros
- [ ] Testar CARs problemáticos em 4 abas
- [ ] Testar notificações são disparadas
- [ ] Testar exportações (PDF + Excel)
- [ ] Testar mobile responsivo
- [ ] Testar logout e redirecionamento para login

---

## 📊 SUMÁRIO

| Fase | Completo | Total | % |
|------|----------|-------|---|
| **1. Banco de Dados** | 9/9 | 9 | ✅ 100% |
| **2. Backend** | 78/78 | 78 | ✅ 100% |
| **3. Frontend** | 0/58 | 58 | ⏳ 0% |
| **4. Polish** | 0/6 | 6 | ⏳ 0% |
| **5. Testes** | 0/10 | 10 | ⏳ 0% |
| **TOTAL** | 87/161 | 161 | **54%** |

---

## 🚀 PRIORIDADE IMEDIATA

1. **HOJE**: Subir Docker + testar endpoint `/admin/login`
2. **AMANHÃ**: Copiar templates de `SETUP_FRONTEND_ADMIN.md` + criar login
3. **PRÓXIMOS DIAS**: Dashboard + Clientes + Pesquisas

---

**Última Atualização:** 2026-04-14
**Próxima Review:** Após completar Frontend
