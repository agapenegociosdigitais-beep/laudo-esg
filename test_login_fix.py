#!/usr/bin/env python3
"""Testar se o login agora funciona corretamente"""
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
    
    # Testar endpoint de login
    print("=== TESTANDO LOGIN ===")
    cmd = """curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "senha": "wrong"}'"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    print("Resposta do backend:", result[:300])
    
    # Ver logs recentes
    print("\n=== LOGS RECENTES (backend) ===")
    stdin, stdout, stderr = ssh.exec_command('docker logs eureka_backend --tail=15', timeout=10)
    logs = stdout.read().decode()
    print(logs)
    
    ssh.close()
    print("\n[✓] Teste concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")