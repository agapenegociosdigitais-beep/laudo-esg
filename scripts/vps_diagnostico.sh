#!/bin/bash

echo "================================"
echo "  DIAGNOSTICO VPS EUREKA TERRA"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================"
echo ""

echo "📦 DOCKER CONTAINERS:"
docker-compose -f /root/eureka-terra/docker-compose.yml ps | grep -E "NAME|postgres|redis|backend|frontend|nginx"
echo ""

echo "📊 HEALTH CHECK - Portas:"
echo -n "Backend (8000): "
curl -s http://localhost:8000/health >/dev/null && echo "✓ OK" || echo "✗ DOWN"

echo -n "Frontend (3000): "
curl -s http://localhost:3000 >/dev/null && echo "✓ OK" || echo "✗ DOWN"

echo -n "PostgreSQL (5432): "
nc -zv localhost 5432 >/dev/null 2>&1 && echo "✓ OK" || echo "✗ DOWN"

echo -n "Redis (6379): "
redis-cli -p 6379 ping >/dev/null 2>&1 && echo "✓ OK" || echo "✗ DOWN"

echo -n "Nginx (80): "
curl -s http://localhost >/dev/null && echo "✓ OK" || echo "✗ DOWN"

echo ""
echo "💾 DISCO:"
df -h | grep -E "Filesystem|/$|eureka"
echo ""

echo "🔍 PROCESSOS IMPORTANTES:"
ps aux | grep -E "docker|nginx|postgres|redis" | grep -v grep | wc -l && echo "Processos ativos encontrados" || echo "Nenhum processo"
echo ""

echo "📝 LOGS RECENTES (últimos erros):"
docker-compose -f /root/eureka-terra/docker-compose.yml logs --tail=5 2>&1 | grep -i "error\|fail" || echo "✓ Sem erros recentes"
echo ""

echo "✅ Diagnostico completo!"
