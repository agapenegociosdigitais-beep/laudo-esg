#!/usr/bin/env python3
"""Corrigir .env na VPS"""
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
    
    # Corrigir o arquivo .env na VPS
    print("[*] Corrigindo .env na VPS...")
    cmd = "cd /root/eureka-terra && sed -i 's|NEXT_PUBLIC_API_URL=http://23.106.45.137/api/v1|NEXT_PUBLIC_API_URL=http://23.106.45.137|g' .env"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err:
        print("Erro:", err)
    
    # Verificar se foi corrigido
    print("\n[*] Verificando correção...")
    stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra && grep NEXT_PUBLIC_API_URL .env', timeout=10)
    result = stdout.read().decode()
    print("Novo valor:", result)
    
    ssh.close()
    print("\n[✓] Correção aplicada na VPS!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")