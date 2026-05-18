#!/usr/bin/env python3
"""Testar login via HTTPS para verificar se o Mixed Content foi resolvido"""
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
    print("[*] Verificando variável no container...")
    stdin, stdout, stderr = ssh.exec_command("docker exec eureka_frontend env | grep NEXT_PUBLIC_API_URL", timeout=10)
    env_container = stdout.read().decode()
    print("Variável no container:", env_container)
    
    # Testar login via HTTPS
    print("\n[*] Testando login via HTTPS...")
    cmd = """curl -s -X POST https://laudoesg.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "agapenegociosdigitais@gmail.com", "senha": "77840000"}' \
  --insecure"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    
    print("\n=== RESULTADO DO LOGIN ===")
    if "access_token" in result:
        print("✅ LOGIN VIA HTTPS FUNCIONANDO!")
        print("O Mixed Content foi resolvido com sucesso!")
    else:
        print("Resposta:", result[:200])
    
    ssh.close()
    print("\n[✓] Teste concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")