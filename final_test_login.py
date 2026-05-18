#!/usr/bin/env python3
"""Teste final - verificar se o login agora funciona sem duplicação de URL"""
import paramiko

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Verificar variável no container
    print("=== VERIFICANDO VARIÁVEL NO CONTAINER ===")
    stdin, stdout, stderr = ssh.exec_command('docker exec eureka_frontend env | grep NEXT_PUBLIC_API_URL', timeout=10)
    env_value = stdout.read().decode()
    print("NEXT_PUBLIC_API_URL:", env_value)
    
    # Testar endpoint de login diretamente
    print("\n=== TESTANDO LOGIN (direto no backend) ===")
    cmd = """curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "senha": "wrong"}'"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    print("Resposta:", result[:200])
    
    # Ver logs recentes para ver se a URL está correta
    print("\n=== LOGS RECENTES (últimos 10 segundos) ===")
    stdin, stdout, stderr = ssh.exec_command('docker logs eureka_backend --since 10s', timeout=10)
    logs = stdout.read().decode()
    if logs:
        print(logs)
    else:
        print("(sem logs recentes)")
    
    ssh.close()
    print("\n[✓] Teste final concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")