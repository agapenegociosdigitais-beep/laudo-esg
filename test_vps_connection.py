#!/usr/bin/env python3
"""Teste de conexão com a VPS"""
import paramiko

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!")
    
    # Executar comandos de verificação
    print("\n[>] Verificando uptime...")
    stdin, stdout, stderr = ssh.exec_command("uptime", timeout=10)
    print(stdout.read().decode())
    
    print("[>] Verificando disco...")
    stdin, stdout, stderr = ssh.exec_command("df -h", timeout=10)
    print(stdout.read().decode())
    
    print("[>] Verificando Docker...")
    stdin, stdout, stderr = ssh.exec_command("docker ps", timeout=10)
    print(stdout.read().decode())
    
    ssh.close()
    print("\n[✓] Conexão encerrada com sucesso!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")