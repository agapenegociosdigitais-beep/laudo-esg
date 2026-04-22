#!/usr/bin/env python3
"""Verifica status do backend na VPS"""
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
    
    # Verificar health do backend
    print("=== HEALTH CHECK ===")
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/health', timeout=10)
    health = stdout.read().decode()
    print(f'Health: {health}')
    
    # Verificar se está respondendo
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs', timeout=10)
    http_code = stdout.read().decode()
    print(f'HTTP Code: {http_code}')
    
    # Verificar containers
    print("\n=== CONTAINERS ===")
    stdin, stdout, stderr = ssh.exec_command('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"', timeout=10)
    containers = stdout.read().decode()
    print(containers)
    
    # Verificar logs recentes do backend
    print("\n=== LOGS RECENTES (backend) ===")
    stdin, stdout, stderr = ssh.exec_command('docker logs eureka_backend --tail=20', timeout=10)
    logs = stdout.read().decode()
    print(logs)
    
    ssh.close()
    print("\n[✓] Conexão encerrada!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")