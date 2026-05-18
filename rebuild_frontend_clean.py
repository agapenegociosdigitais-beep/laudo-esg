#!/usr/bin/env python3
"""Rebuild completo e limpo do frontend para garantir que a nova variável seja aplicada"""
import paramiko
import time

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Passo 1: Parar containers
    print("[1/5] Parando containers...")
    stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra && docker-compose down', timeout=60)
    print(stdout.read().decode())
    
    # Passo 2: Remover imagem antiga do frontend (forçar rebuild limpo)
    print("\n[2/5] Removendo imagem antiga do frontend...")
    stdin, stdout, stderr = ssh.exec_command('docker rmi eureka-terra-frontend:latest 2>/dev/null || echo "Imagem já removida"', timeout=30)
    print(stdout.read().decode())
    
    # Passo 3: Fazer build com a variável explicitamente definida
    print("\n[3/5] Fazendo build do frontend com NEXT_PUBLIC_API_URL correto...")
    build_cmd = 'cd /root/eureka-terra && docker-compose build --no-cache --build-arg NEXT_PUBLIC_API_URL=http://23.106.45.137 frontend'
    stdin, stdout, stderr = ssh.exec_command(build_cmd, timeout=600)
    output = stdout.read().decode()
    print("Build concluído! Últimas linhas:")
    print('\n'.join(output.split('\n')[-20:]))  # Últimas 20 linhas
    
    # Passo 4: Subir containers novamente
    print("\n[4/5] Subindo containers...")
    stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra && docker-compose up -d', timeout=120)
    print(stdout.read().decode())
    
    # Passo 5: Aguardar e verificar
    print("\n[5/5] Aguardando 30 segundos e verificando...")
    time.sleep(30)
    
    stdin, stdout, stderr = ssh.exec_command('docker exec eureka_frontend env | grep NEXT_PUBLIC_API_URL', timeout=10)
    env_value = stdout.read().decode()
    print("Variável no container:", env_value)
    
    stdin, stdout, stderr = ssh.exec_command('docker logs eureka_frontend --tail=5', timeout=10)
    logs = stdout.read().decode()
    print("\nLogs do frontend:", logs)
    
    ssh.close()
    print("\n[✓] Rebuild completo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")