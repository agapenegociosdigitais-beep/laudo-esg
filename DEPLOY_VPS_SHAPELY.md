# 🚀 DEPLOY SHAPELY PARA VPS

## Status

✅ **Código commitado no GitHub**
- Commit: `148b1f6` 
- Arquivo: `backend/app/services_novo/desmatamento_service.py`
- Feature: Interseção geométrica real com Shapely

❌ **Automação SSH falhou** - execute manualmente na VPS

---

## Opção 1: SSH Interativa (Recomendado)

```bash
# 1. Conectar na VPS
ssh root@23.106.45.137
# Copie e cole a senha quando pedir: JVghqGUersYW6h8Q

# 2. Fazer deploy
cd /root/eureka-terra

# 3. Pull do código novo
git pull origin main

# Esperado: Fast-forward (mudanças do Shapely)
# OU "Already up to date." se já tem

# 4. Parar containers
docker-compose down

# 5. Rebuild backend (leva ~3 min)
docker-compose build --no-cache backend

# Última linha deve ser: "naming to docker.io/library/eureka-terra-backend:latest"

# 6. Subir containers
docker-compose up -d

# 7. Aguardar 45 segundos
sleep 45

# 8. Verificar se backend está online
curl http://localhost/health

# Esperado resposta com: "ok"

# 9. Ver containers rodando
docker-compose ps

# Todos devem estar "Up"
```

---

## Opção 2: Copiar e Colar Tudo de Uma Vez

Cole isto inteiro no terminal SSH da VPS:

```bash
cd /root/eureka-terra && \
git pull origin main && \
docker-compose down && \
docker-compose build --no-cache backend && \
docker-compose up -d && \
echo "Aguardando 45s..." && \
sleep 45 && \
echo "=== Health Check ===" && \
curl http://localhost/health && \
echo "" && \
echo "=== Containers ===" && \
docker-compose ps
```

---

## Opção 3: Script na VPS

Crie arquivo na VPS:

```bash
# SSH na VPS
ssh root@23.106.45.137

# Criar arquivo
cat > /root/deploy-shapely.sh << 'EOF'
#!/bin/bash
cd /root/eureka-terra
git pull origin main
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
sleep 45
echo "Health Check:"
curl http://localhost/health
echo ""
echo "Containers:"
docker-compose ps
EOF

chmod +x /root/deploy-shapely.sh

# Executar
/root/deploy-shapely.sh
```

---

## ✅ Checklist pós-deploy

- [ ] SSH conectado em `root@23.106.45.137`
- [ ] `git pull origin main` retornou mudanças
- [ ] `docker-compose down` executou
- [ ] `docker-compose build --no-cache backend` completou
- [ ] `docker-compose up -d` iniciou
- [ ] Aguardou 45 segundos
- [ ] `curl http://localhost/health` retornou `{"status":"ok"}`
- [ ] `docker-compose ps` mostra todos "Up"

---

## 🔍 Verificação: Shapely está ativo?

Após deploy, execute na VPS:

```bash
docker-compose logs backend | grep -i "shapely\|intersecao\|PRODES" | tail -5
```

Deve aparecer algo como:
```
PRODES (intersecção real): 6 registros, 33.07 ha para Amazônia
```

---

## 🆘 Se algo der errado

### Logs
```bash
ssh root@23.106.45.137
docker-compose logs backend -f --tail=50
# Ctrl+C para sair
```

### Restart manual
```bash
docker-compose restart backend
```

### Reset completo
```bash
docker-compose down
docker-compose up -d --build
```

---

## 📍 URLs após Deploy

- **Frontend:** http://laudoesg.com
- **API:** http://laudoesg.com/api/v1/
- **Health:** http://localhost/health (apenas VPS)

---

## 📊 Mudanças Implementadas

**Arquivo:** `backend/app/services_novo/desmatamento_service.py`

```python
# ✅ Adicionado no topo
from shapely.geometry import shape
from shapely.ops import unary_union

# ✅ Na função _consultar_terrabrasilis():
car_geom = shape(geojson)  # Geometria CAR

for f in feats:
    prodes_geom = shape(f.get("geometry", {}))
    intersecao = car_geom.intersection(prodes_geom)  # Interseção real
    area_ha = round(intersecao.area / 10000, 4)  # m² → ha
    percentual_dentro = (area_ha / area_prodes_ha) * 100
```

**Resultado:** Cálculo preciso de desmatamento com interseção geométrica real (Shapely).

---

**Pronto para deploy! 🚀**
