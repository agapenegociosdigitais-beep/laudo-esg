# Eureka Terra — Backup e Restauração

**Data:** 15/05/2026  
**Versão:** Pós-migração para GeoServer Nacional Unificado

---

## Resumo do que foi feito

O projeto foi migrado de 7 APIs externas instáveis para **1 único GeoServer nacional** que cobre 100% dos dados necessários:

```
Fonte única: https://geoserverdw.apps.geoapplications.net/geoserver/wfs/
```

### Arquivos alterados/criados

| Arquivo | Ação | Descrição |
|---|---|---|
| `backend/app/models/cache_local.py` | Criado | 10 modelos SQLAlchemy para tabelas de cache local |
| `backend/app/services/cache_local_service.py` | Criado | Consultas espaciais ST_Intersects + busca CAR por código |
| `scripts/sync_shapefiles.py` | Criado | Baixa shapefiles do GeoServer e importa no PostGIS |
| `scripts/download_novo_geoserver.py` | Criado | Baixa shapefiles para pasta SHAPEFILES/ |
| `scripts/download_shapefiles.py` | Criado | Download alternativo (fontes antigas) |
| `scripts/crontab.txt` | Criado | Configuração de cron para sync automático |
| `scripts/check_sync_status.py` | Criado | Verifica status das tabelas |
| `backend/scripts/migrations/002_cache_local_indexes.sql` | Criado | Índices GiST para tabelas de cache |
| `backend/app/services/car_service.py` | Modificado | Cache local primeiro, fallback APIs, sem Exception 500 |
| `backend/app/services/desmatamento_service.py` | Modificado | Cache PRODES local (ST_Intersects) + fallback API |
| `backend/app/services/embargos_service.py` | Modificado | Cache unificado IBAMA+SEMAS+ICMBIO; corrigidos exception handlers vazios; main_class fix |
| `backend/app/services/areas_protegidas_service.py` | Modificado | Cache UC + TI local; fallbacks explícitos |
| `backend/app/services/conformidade_service.py` | Restaurado | Recuperado completo (estava truncado); cache quilombola + assentamento |
| `backend/app/core/database.py` | Modificado | Importa cache_local; executa migrations SQL |
| `Makefile` | Modificado | Comandos `make sync`, `make sync-prodes`, `make sync-embargos` |
| `.env` | Modificado | NEXT_PUBLIC_API_URL apontando para localhost |

### Bugs corrigidos

1. `embargos_service.py`: CQL `main_class='desmatamento'` (minúsculo) perdia dados 2021+
2. `embargos_service.py`: 3 exception handlers vazios retornavam None silenciosamente
3. `conformidade_service.py`: truncado — faltavam `verificar_assentamentos`, `verificar_trabalho_escravo`, `calcular_balanco_ambiental`
4. `areas_protegidas_service.py`: `verificar_sobreposicao_uc/ti` retornavam None implícito
5. `car_service.py`: Exception não tratada causava 500 quando APIs externas offline

---

## Shapefiles baixados

```
SHAPEFILES/                         Total: ~750 MB
├── EMBARGOS/                       14 MB    workspace_sicar:vw_sicar_embargos
├── TERRAS_INDIGENAS/                5 MB    workspace_sicar:vw_sicar_terras_indigenas
├── UNIDADES_CONSERVACAO/            6 MB    workspace_sicar:vw_sicar_unidades_conservacao
├── QUILOMBOLAS/                   0.6 MB    workspace_sicar:vw_sicar_areas_quilombolas
├── ASSENTAMENTOS/                   9 MB    workspace_sicar:vw_sicar_assentamentos
├── PRODES/                        202 MB    workspace_sicar:mv_desmatamento_prodes_2008
├── AUTOS_INFRACAO/                  2 MB    workspace_sicar:vw_sicar_autos_de_infracao
├── FLORESTAS_PUBLICAS/             51 MB    workspace_sicar:vw_florestas_publicas_2024
├── ALERTAS_DETER/                  92 MB    workspace_fiscalizacao_inteligente:vw_alertas_deter
├── CAR_ATIVO/                      29 MB    workspace_sicar:vw_car_ativo
├── PRODES_INPE/                    66 MB    (3 biomas TerraBrasilis — backup)
├── EMBARGOS_IBAMA/                233 MB    (GeoJSON paginado — backup)
├── QUILOMBOLAS_INCRA/               2 MB    (fonte antiga — backup)
├── TERRAS_INDIGENAS_FUNAI/         21 MB    (fonte antiga — backup)
└── ASSENTAMENTOS_INCRA/            31 MB    (fonte antiga — backup)
```

---

## Banco de dados — Tabelas e registros

| Tabela | Registros | Fonte |
|---|---|---|
| `cache_prodes` | 384.297 | Desmatamento PRODES 2008+ |
| `cache_alertas_deter` | 176.273 | Alertas DETER |
| `cache_car_ativo` | 65.327 | CARs ativos do Pará |
| `cache_embargos` | 16.439 | Embargos IBAMA+SEMAS+ICMBIO |
| `cache_florestas_publicas` | 3.051 | Florestas Públicas SFB |
| `cache_assentamentos` | 1.116 | Assentamentos INCRA+ITERPA |
| `cache_quilombolas` | 188 | Quilombolas ITERPA+INCRA |
| `cache_unidades_conservacao` | 110 | UC (MMA+ICMBIO+IDEFLOR) |
| `cache_terras_indigenas` | 60 | TI (FUNAI) |
| `cache_autos_infracao` | 1 | Autos de Infração (incompleto) |
| **TOTAL** | **646.862** | |

---

## Como restaurar do zero

### Pré-requisitos
- Docker + Docker Compose
- Git
- ~5 GB de espaço livre

### Passo 1: Subir containers
```bash
cd C:\projects\eureka-terra
docker compose up -d postgres redis
# Aguardar ~10s até postgres ficar healthy
docker compose up -d backend frontend
```

### Passo 2: Criar usuário admin (se não existir)
```bash
docker exec eureka_postgres psql -U eureka -d eureka_db -c "
  INSERT INTO admin_users (id, email, password_hash, role)
  VALUES (gen_random_uuid(), 'admin@eurekaterra.com',
          '\$2b\$12\$gWD.BPOpVgFU4m9IyPKguuqzJxuibiPbfdcj6Ko.lQ5NYuAZ95iAG',
          'super_admin')
  ON CONFLICT (email) DO NOTHING;
"
```

### Passo 3: Sincronizar dados geoespaciais
```bash
# Copia o script de sync para dentro do backend
cp scripts/sync_shapefiles.py backend/scripts/sync_shapefiles.py

# Instala dependência extra no backend
docker exec eureka_backend pip install psycopg2-binary geoalchemy2 -q

# Executa sync (baixa ~400 MB e importa no PostGIS)
docker exec eureka_backend python scripts/sync_shapefiles.py
```

### Passo 4: Verificar
```bash
# Contar registros
docker exec eureka_postgres psql -U eureka -d eureka_db -c "
  SELECT 'cache_prodes' AS t, COUNT(*) FROM cache_prodes
  UNION ALL SELECT 'cache_car_ativo', COUNT(*) FROM cache_car_ativo
  UNION ALL SELECT 'cache_embargos', COUNT(*) FROM cache_embargos
  ORDER BY t;
"

# Testar API
curl http://localhost:8000/health
```

### Passo 5: Configurar sync automático (VPS)
```bash
# Copiar crontab
crontab scripts/crontab.txt
# Verificar
crontab -l
```

---

## Camadas do GeoServer Nacional

| # | Layer | Descrição | Órgão |
|---|---|---|---|
| 1 | `workspace_sicar:vw_sicar_embargos` | Embargos | IBAMA+SEMAS+ICMBIO |
| 2 | `workspace_sicar:vw_sicar_terras_indigenas` | Terras Indígenas | FUNAI |
| 3 | `workspace_sicar:vw_sicar_unidades_conservacao` | Unidades de Conservação | MMA+ICMBIO+IDEFLOR |
| 4 | `workspace_sicar:vw_sicar_areas_quilombolas` | Áreas Quilombolas | ITERPA+INCRA |
| 5 | `workspace_sicar:vw_sicar_assentamentos` | Assentamentos | INCRA+ITERPA |
| 6 | `workspace_sicar:mv_desmatamento_prodes_2008` | Desmatamento PRODES | INPE |
| 7 | `workspace_sicar:vw_sicar_autos_de_infracao` | Autos de Infração | IBAMA+SEMAS |
| 8 | `workspace_sicar:vw_florestas_publicas_2024` | Florestas Públicas | SFB |
| 9 | `workspace_fiscalizacao_inteligente:vw_alertas_deter` | Alertas DETER | INPE |
| 10 | `workspace_sicar:vw_car_ativo` | CARs Ativos | PA |

---

## Credenciais

| Recurso | URL | Usuário | Senha |
|---|---|---|---|
| Frontend | http://localhost:3000 | admin@eurekaterra.com | Admin@123456 |
| API Swagger | http://localhost:8000/docs | — | — |
| Postgres | localhost:5432 | eureka | eurekapass |
| Redis | localhost:6379 | — | — |

---

## Comandos úteis

```bash
make help           # Lista todos os comandos
make sync           # Sincroniza todas as camadas do GeoServer
make sync-embargos  # Sincroniza só embargos
make up             # Sobe todos os containers
make build          # Rebuild completo
make logs           # Logs em tempo real
make clean          # Remove containers e volumes
make status         # Health check
```

---

## Notas importantes

- **Shapefile DBF**: limita nomes de coluna a 10 caracteres. O mapeamento no sync já trata isso.
- **Geometrias 3D**: o sync aplica `ST_Force2D(ST_Multi(...))` automaticamente.
- **SEMAS-PA**: GeoServer antigo (`car.semas.pa.gov.br/geoserver`) foi desligado. O portal novo (`portal-servicos-sistemas.semas.pa.gov.br`) exige login.
- **CNUC/MMA**: WFS offline. Os dados de UC vêm do GeoServer nacional.
- **Fontes indisponíveis**: PRODES Cerrado (layer específica retorna 400 no bulk download).
- **Sincronização**: Rodar `make sync` a cada 3 dias na VPS. Cron configurado em `scripts/crontab.txt`.
