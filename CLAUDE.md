# Eureka Terra — Contexto do Projeto para Claude Code

## O que é este projeto
Plataforma SaaS de análise ESG para propriedades rurais brasileiras.
O usuário é produtor/consultor que precisa verificar conformidade ambiental de CARs antes de financiamento, exportação para UE (EUDR) ou comercialização de soja.

## Stack técnica
- **Backend:** FastAPI (Python 3.11) + SQLAlchemy async + asyncpg + PostgreSQL/PostGIS
- **Frontend:** Next.js 14 (TypeScript) + Tailwind CSS
- **Infra:** Docker Compose (postgres, redis, backend, frontend, nginx)
- **Acesso local:** http://127.0.0.1:3000 (frontend) | http://127.0.0.1:8000 (API)

## Regra obrigatória após qualquer alteração
**SEMPRE fazer build e restart ao final de cada modificação — sem exceção:**
```bash
docker-compose build --no-cache backend   # se backend foi alterado
docker-compose build --no-cache frontend  # se frontend foi alterado
docker-compose up -d                      # restart
```
O usuário acessa pelo endereço web e precisa ver as mudanças imediatamente.

## Estrutura de pastas importantes
```
eureka-terra/
├── backend/
│   └── app/
│       ├── api/endpoints/
│       │   ├── analises.py       # pipeline ESG completa (background)
│       │   └── propriedades.py   # busca CAR + cache local
│       ├── core/
│       │   └── config.py         # CORS, JWT, settings — ALLOWED_ORIGINS inclui 127.0.0.1:3000
│       ├── models/
│       │   └── analise.py        # JSONB: embargo_ibama, embargo_semas, sobreposicao_uc/ti,
│       │                         #        dados_desmatamento, resultado_conformidade
│       ├── schemas/
│       │   └── analise.py        # AnaliseResposta expõe dados_desmatamento
│       └── services/
│           ├── car_service.py        # orquestra SEMAS-PA → SICAR → simulação
│           ├── semas_service.py      # GeoServer SEMAS-PA (CARs do Pará)
│           ├── sicar_service.py      # GeoServer SICAR nacional
│           ├── desmatamento_service.py  # PRODES/TerraBrasilis com intersecção real
│           ├── conformidade_service.py  # quilombola, assentamento, trabalho escravo, RL/APP
│           ├── embargos_service.py      # IBAMA CTF, SEMAS-PA, marco UE
│           └── areas_protegidas_service.py  # UC (CNUC), TI (FUNAI)
├── frontend/
│   └── src/
│       ├── services/api.ts       # BASE_URL: SSR=backend:8000, browser=NEXT_PUBLIC_API_URL
│       ├── types/index.ts        # interfaces TS: Analise, DadosDesmatamento, etc.
│       └── components/Dashboard/
│           ├── ComplianceStatus.tsx  # painel ESG com todos os cards
│           └── PropertyInfo.tsx      # card do CAR com alertas de status
├── .env                          # NEXT_PUBLIC_API_URL=http://localhost:8000
└── docker-compose.yml            # ports: 3000, 8000 (não expose:)
```

## Fontes de dados externas integradas

### CAR / Situação do imóvel
- **SEMAS-PA GeoServer:** `https://car.semas.pa.gov.br/geoserver/wfs` — layer `secar-pa:imovel`
  - Só para CARs do Pará (PA)
  - CAR normalizado SEM pontos: `PA-1501451-110F7A95...` (não `PA-1501451-110F.7A95...`)
  - Campos: `cod_imovel`, `ind_status_imovel` (AT/PE/CA/SU), `des_condicao`, `num_area_imovel`, `nom_imovel`
- **SICAR nacional GeoServer:** `https://geoserver.car.gov.br/geoserver/sicar/wfs`
  - Para todos os estados

### PRODES (Desmatamento)
- **TerraBrasilis WFS:** `https://terrabrasilis.dpi.inpe.br/geoserver/ows`
- Layers por bioma:
  - Amazônia: `prodes-legal-amz:yearly_deforestation`
  - Cerrado: `prodes-cerrado-nb:yearly_deforestation`
  - Mata Atlântica: `prodes-mata-atlantica-nb:yearly_deforestation`
- **ATENÇÃO CRÍTICA:** `main_class` varia por ano:
  - Até 2020: `'desmatamento'` (minúsculo)
  - 2021+: `'DESMATAMENTO'` (maiúsculo)
  - **NÃO filtrar por main_class no CQL** — filtrar no Python com `.lower()`
- Algoritmo: BBOX → interseção Shapely → área geodésica pyproj → agrupa por ano
- count=500 (não 100, para não truncar)

### Embargos
- **IBAMA CTF:** API pública
- **SEMAS-PA SIMLAM:** API estadual

### Áreas Protegidas
- **UC:** CNUC/MMA GeoServer
- **TI:** FUNAI GeoServer

### Conformidade Social
- **Quilombolas:** INCRA WFS `territorio_quilombola_portaria`
- **Assentamentos:** INCRA WFS `projetoassentamento`
- **Trabalho Escravo:** Lista Suja MTE — transparencia.gov.br

## Status do CAR — lógica de exibição (PropertyInfo.tsx)
- `ATIVO/Ativo` → verde, análise válida
- `PENDENTE/Pendente/INSCRITO` → alerta amarelo, mensagem simplificada
- `SUSPENSO/Suspenso` → alerta laranja
- `INATIVO/Inativo` → alerta vermelho
- `CANCELADO/Cancelado` → alerta vermelho forte, análise inválida
- Cache local sempre re-consulta fonte real para manter status atualizado

## Campos JSONB no banco (tabela analises)
- `embargo_ibama`, `embargo_semas` → dict com embargado, orgao, numero, area, motivo
- `sobreposicao_uc`, `sobreposicao_ti` → dict com sobreposicao_detectada, nome_area, categoria
- `dados_desmatamento` → `{total_registros, bioma, metodo, registros_por_ano: [{ano, area_ha}], anos_detectados}`
- `resultado_conformidade` → `{quilombola, assentamento, trabalho_escravo, balanco_ambiental, marco_ue, bioma, estado}`

## Frontend — cards de conformidade (ComplianceStatus.tsx)
- `LinkConsulta` component em todos os cards com intercorrência
- PRODES: tabela detalhada por ano (só quando `dados_desmatamento.registros_por_ano` existe)
- Fundo vermelho no card PRODES quando desmatamento detectado
- Assentamentos/Quilombolas: lista com nomes em bullet points

## Problemas já resolvidos (não regredir)
1. **CORS 127.0.0.1** — config.py tem `http://127.0.0.1:3000` nas ALLOWED_ORIGINS
2. **NEXT_PUBLIC_API_URL** — baked no build; raiz `.env` define `http://localhost:8000`
3. **PRODES 2021 ausente** — era filtrado pelo CQL `main_class='desmatamento'`; removido
4. **Status sempre ATIVO** — sicar_service retornava simulação quando sem geometria; corrigido
5. **Data embargo como timestamp** — removido `dados.data_embargo` do card
6. **Assentamento sem detalhes** — conformidade_service extrai nome+município+SIPRA com fallback

## Como subir o ambiente do zero
```bash
cd C:\Users\benja\Desktop\eureka-terra
docker-compose up -d postgres redis
# aguardar ~10s
docker-compose up -d backend frontend
```
