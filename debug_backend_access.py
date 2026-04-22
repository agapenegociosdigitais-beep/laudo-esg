#!/usr/bin/env python3
"""Debug acesso ao backend - testa endpoints e mostra logs"""
import paramiko
import time

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Testar endpoints principais
    endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/docs",
        "http://localhost:8000/redoc",
        "http://localhost:8000/api/v1/propriedades",
        "http://localhost:8000/api/v1/analises"
    ]
    
    print("=== TESTANDO ENDPOINTS ===")
    for endpoint in endpoints:
        # Testar apenas o código HTTP
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {endpoint}"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        http_code = stdout.read().decode().strip()
        
        # Testar conteúdo (primeiros 100 chars)
        cmd = f"curl -s {endpoint} | head -c 100"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        content = stdout.read().decode().strip()
        
        print(f"{endpoint}: HTTP {http_code} | {content}")
    
    # Ver logs em tempo real (últimos 30 segundos)
    print("\n=== LOGS RECENTES (últimos 30s) ===")
    since = int(time.time()) - 30
    stdin, stdout, stderr = ssh.exec_command(f'docker logs eureka_backend --since {since}s', timeout=10)
    logs = stdout.read().decode()
    if logs:
        print(logs)
    else:
        print("(sem logs recentes)")
    
    # Verificar rotas disponíveis
    print("\n=== ROTAS DISPONÍVEIS (openapi.json) ===")
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/openapi.json', timeout=10)
    openapi = stdout.read().decode()
    if openapi:
        # Extrair rotas manualmente
        import json
        try:
            data = json.loads(openapi)
            paths = sorted(data.get('paths', {}).keys())
            for path in paths:
                print(path)
        except:
            print("(erro ao parsear openapi.json)")
    else:
        print("(não foi possível obter rotas)")
    
    ssh.close()
    print("\n[✓] Conexão encerrada!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")