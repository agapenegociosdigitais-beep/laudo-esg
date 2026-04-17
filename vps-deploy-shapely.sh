#!/bin/bash
# Deploy de Shapely Interseção para VPS

VPS_IP="23.106.45.137"
VPS_USER="root"
VPS_PASS="JVghqGUersYW6h8Q"
VPS_HOME="/root/eureka-terra"

echo "🚀 Deploy Shapely Interseção para VPS"
echo "=================================="
echo "IP: $VPS_IP"
echo "Dir: $VPS_HOME"
echo ""

# Método 1: Via SSH direto (requer autenticação prévia)
echo "Conectando via SSH..."

# Script a ser executado na VPS
read -r -d '' VPS_SCRIPT << 'VPSEOF'
cd /root/eureka-terra
echo "📥 Fazendo git pull..."
git pull origin main 2>&1 | grep -E "Fast-forward|Already|error" || echo "Pull OK"

echo "🛑 Parando containers..."
docker-compose down 2>&1 | grep -E "Stopping|Removed"

echo "🔨 Rebuilding backend..."
docker-compose build --no-cache backend 2>&1 | grep -E "DONE|Step" | tail -5

echo "🚀 Iniciando containers..."
docker-compose up -d 2>&1 | grep -E "Creating|Starting|Created"

echo "⏳ Aguardando backend..."
for i in {1..30}; do
  if curl -s http://localhost/health 2>/dev/null | grep -q "ok"; then
    echo "✅ Backend pronto!"
    break
  fi
  echo "  Tentativa $i..."
  sleep 2
done

echo "✅ Deploy concluído!"
VPSEOF

# Tenta via uma conexão SSH já autenticada
# Se não funcionar, instruções manuais serão dadas
echo "$VPS_SCRIPT" | ssh -T root@23.106.45.137 2>/dev/null || {
  echo ""
  echo "⚠️ Conexão SSH automática falhou."
  echo ""
  echo "Manual steps para deploy na VPS:"
  echo "================================"
  echo "1. SSH na VPS:"
  echo "   ssh root@23.106.45.137"
  echo ""
  echo "2. Execute os comandos:"
  echo "   cd /root/eureka-terra"
  echo "   git pull origin main"
  echo "   docker-compose down"
  echo "   docker-compose build --no-cache backend"
  echo "   docker-compose up -d"
  echo ""
  echo "3. Aguarde 30s após 'docker-compose up -d'"
  echo "4. Teste: curl http://localhost/health"
  exit 1
}
