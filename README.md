# 🌱 Eureka Terra

Plataforma SaaS para análise de conformidade ambiental (ESG) de propriedades rurais brasileiras.

Analise propriedades pelo número do **CAR**, visualize o polígono no mapa, calcule **NDVI** via satélite e gere relatórios de conformidade com **Moratória da Soja** e **EUDR** em minutos.

---

## Funcionalidades do MVP

| Funcionalidade | Status |
|---|---|
| Busca por número do CAR (SICAR) | ✅ |
| Visualização do polígono no mapa (Leaflet + OSM) | ✅ |
| Cálculo de NDVI (Sentinel-2 / Copernicus) | ✅ |
| Verificação Moratória da Soja | ✅ |
| Verificação EUDR (UE 2023/1115) | ✅ |
| Score ESG (0-100) | ✅ |
| Geração de relatório PDF (WeasyPrint) | ✅ |
| Autenticação JWT | ✅ |

---

## Stack

- **Back-end:** Python 3.11 + FastAPI + SQLAlchemy (async) + PostGIS
- **Cache:** Redis
- **Front-end:** Next.js 14 + TypeScript + Tailwind CSS
- **Mapas:** Leaflet.js + OpenStreetMap (gratuito, sem token)
- **Gráficos:** Recharts
- **Geoespacial:** GeoPandas, Rasterio, Shapely
- **PDF:** WeasyPrint + Jinja2
- **Infraestrutura:** Docker + Docker Compose

---

## Fontes de Dados

| Fonte | Dados | Acesso |
|---|---|---|
| SICAR/MAPA | Polígonos CAR | Público |
| Copernicus/ESA | Imagens Sentinel-2 (NDVI) | Gratuito (registro) |
| PRODES/INPE via TerraBrasilis | Desmatamento | Público |
| MapBiomas | Cobertura e uso do solo | Token gratuito |

---

## Pré-requisitos

- Docker e Docker Compose instalados
- (Opcional) Conta no [Copernicus Data Space](https://dataspace.copernicus.eu) para dados NDVI reais
- (Opcional) Token do [MapBiomas](https://mapbiomas.org) para cobertura do solo

---

## Instalação e Execução

### 1. Clone e configure o ambiente

```bash
git clone https://github.com/seu-usuario/eureka-terra.git
cd eureka-terra

# Copia o arquivo de configuração
cp .env.example .env

# Edite o .env com suas credenciais
nano .env
```

### 2. Inicie os containers

```bash
docker-compose up --build -d
```

### 3. Acesse a plataforma

| Serviço | URL |
|---|---|
| **Front-end** | http://localhost:3000 |
| **API (Swagger)** | http://localhost:8000/docs |
| **API (ReDoc)** | http://localhost:8000/redoc |

---

## Configuração das Variáveis de Ambiente

```env
# Banco de Dados
DATABASE_URL=postgresql://user:password@localhost:5432/eureka_db

# Redis
REDIS_URL=redis://localhost:6379

# Segurança JWT
SECRET_KEY=sua_chave_secreta_aqui
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Copernicus (imagens Sentinel-2 reais)
# Registro gratuito em: https://dataspace.copernicus.eu
COPERNICUS_USER=seu_usuario
COPERNICUS_PASSWORD=sua_senha

# MapBiomas (cobertura do solo)
MAPBIOMAS_TOKEN=seu_token

# Ambiente
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000
```

> **Sem credenciais:** a plataforma funciona normalmente em modo simulado,
> com dados realistas gerados deterministicamente por bioma/localização.

---

## Estrutura do Projeto

```
eureka-terra/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/     # auth, propriedades, analises, relatorios
│   │   ├── core/              # config, database, security
│   │   ├── models/            # usuario, propriedade, analise, relatorio
│   │   ├── schemas/           # validação Pydantic
│   │   ├── services/          # car, satellite, ndvi, desmatamento, relatorio
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/               # layout, page, login, register, dashboard
│   │   ├── components/        # Map, Dashboard, Relatorio
│   │   ├── services/          # api.ts, auth.ts
│   │   └── types/             # index.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Regulações Verificadas

### Moratória da Soja (MSM)
Acordo voluntário de 2006 entre as principais tradings de soja, renovado anualmente.
Proíbe a **comercialização de soja** produzida em áreas da **Amazônia** desmatadas
após **24 de julho de 2008**.

### EUDR — Regulamento (UE) 2023/1115
Em vigor a partir de 30/12/2024 para grandes operadores.
Exige **rastreabilidade geoespacial** e ausência de desmatamento após **31/12/2020**
para: soja, gado, café, cacau, óleo de palma, madeira, borracha e derivados.

---

## API — Endpoints Principais

```
POST /api/v1/auth/registrar       Cria conta
POST /api/v1/auth/login           Login → token JWT
GET  /api/v1/auth/me              Perfil do usuário

POST /api/v1/propriedades/buscar-car   Busca propriedade pelo CAR
GET  /api/v1/propriedades/{id}         Dados da propriedade

POST /api/v1/analises/            Inicia análise (background)
GET  /api/v1/analises/{id}        Resultado da análise

POST /api/v1/relatorios/gerar     Gera PDF
GET  /api/v1/relatorios/{id}/download  Download do PDF
```

---

## Licença

MIT © 2024 Eureka Terra
