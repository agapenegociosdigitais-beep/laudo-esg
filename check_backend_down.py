#!/usr/bin/env python3
"""Verificar se o backend caiu e diagnosticar o problema"""
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
    
    # Verificar containers
    print("=== CONTAINERS DOCKER ===")
    stdin, stdout, stderr = ssh.exec_command('docker ps --format "table {{.Names}}\t{{.Status}}"', timeout=10)
    containers = stdout.read().decode()
    print(containers)
    
    # Verificar se backend está rodando
    print("\n=== STATUS DO BACKEND ===")
    stdin, stdout, stderr = ssh.exec_command('docker inspect eureka_backend --format="{{.State.Status}}"', timeout=10)
    status = stdout.read().decode().strip()
    print(f"Status: {status}")
    
    if status != "running":
        print("\n[!] Backend não está rodando! Verificando logs...")
        stdin, stdout, stderr = ssh.exec_command('docker logs eureka_backend --tail=50', timeout=10)
        logs = stdout.read().decode()
        print("\nÚltimos logs:")
        print(logs)
        
        print("\n[*] Tentando reiniciar backend...")
        stdin, stdout, stderr = ssh.exec_command('docker restart eureka_backend', timeout=30)
        restart_result = stdout.read().decode()
        print(restart_result if restart_result else "Backend reiniciado!")
    else:
        # Testar health endpoint
        print("\n[*] Testando health endpoint...")
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/health', timeout=10)
        health = stdout.read().decode()
        print(f"Health: {health}")
        
        # Verificar logs recentes
        print("\n[*] Logs recentes:")
        stdin, stdout, stderr = ssh.exec_command('docker logs eureka_backend --tail=20', timeout=10)
        logs = stdout.read().decode()
        print(logs)
    
    ssh.close()
    print("\n[✓] Verificação concluída!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")