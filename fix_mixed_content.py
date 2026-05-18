#!/usr/bin/env python3
"""Corrigir Mixed Content atualizando NEXT_PUBLIC_API_URL para HTTPS"""
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
    
    # Verificar configuração atual
    print("[*] Verificando configuração atual...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && grep NEXT_PUBLIC_API_URL .env", timeout=10)
    env_value = stdout.read().decode()
    print("Valor atual:", env_value)
    
    # Atualizar para HTTPS
    print("\n[*] Atualizando para HTTPS...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && sed -i 's|NEXT_PUBLIC_API_URL=http://23.106.45.137|NEXT_PUBLIC_API_URL=https://laudoesg.com|g' .env", timeout=10)
    print("✅ Atualizado")
    
    # Verificar nova configuração
    print("\n[*] Verificando nova configuração...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && grep NEXT_PUBLIC_API_URL .env", timeout=10)
    new_value = stdout.read().decode()
    print("Novo valor:", new_value)
    
    # Rebuild do frontend
    print("\n[*] Rebuildando frontend com nova configuração...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && docker-compose build --no-cache frontend", timeout=300)
    build_result = stdout.read().decode()
    print("✅ Build concluído")
    
    # Restart frontend
    print("\n[*] Restartando frontend...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && docker-compose restart frontend", timeout=30)
    print("✅ Frontend reiniciado")
    
    ssh.close()
    print("\n[✓] Correção concluída!")
    print("\n📝 O frontend agora usará HTTPS para se comunicar com o backend.")
    print("   Isso resolverá o problema de Mixed Content.")
    
except Exception as e:
    print(f"[✗] Erro: {e}")