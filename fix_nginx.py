#!/usr/bin/env python3
"""Corrigir configuração do nginx"""
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
    
    # Restaurar backup
    print("[*] Restaurando configuração original...")
    stdin, stdout, stderr = ssh.exec_command("cp /root/eureka-terra/nginx/nginx.conf.backup /root/eureka-terra/nginx/nginx.conf", timeout=10)
    print("✅ Configuração restaurada")
    
    # Reiniciar nginx
    print("\n[*] Reiniciando nginx...")
    stdin, stdout, stderr = ssh.exec_command("docker restart eureka_nginx", timeout=30)
    print("✅ Nginx reiniciado")
    
    # Verificar status
    print("\n[*] Verificando status...")
    stdin, stdout, stderr = ssh.exec_command("docker ps --filter name=eureka_nginx --format '{{.Status}}'", timeout=10)
    status = stdout.read().decode().strip()
    print(f"Status: {status}")
    
    # Testar
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:80/health", timeout=10)
    test = stdout.read().decode()
    print(f"Teste HTTP: {test}")
    
    ssh.close()
    print("\n[✓] Correção concluída!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")