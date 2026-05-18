#!/usr/bin/env python3
"""Verificar hash atual no banco de dados"""
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
    
    # Verificar hash atual
    print("[*] Verificando hash atual no banco...")
    cmd = "docker exec eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, LEFT(senha_hash, 50) as hash_preview FROM usuarios WHERE email='agapenegociosdigitais@gmail.com';\""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    print(result)
    
    # Ver logs do backend
    print("\n[*] Verificando logs do backend...")
    stdin, stdout, stderr = ssh.exec_command("docker logs eureka_backend --tail=15 2>&1", timeout=10)
    logs = stdout.read().decode()
    print("Logs recentes:")
    print(logs)
    
    ssh.close()
    print("\n[✓] Verificação concluída!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")