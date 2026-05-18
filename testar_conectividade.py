#!/usr/bin/env python3
"""Testar conectividade com a VPS e serviços"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print('=== TESTANDO CONEXÃO COM A VPS ===')
try:
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    print('[✓] Conexão SSH estabelecida com sucesso!')
    
    # Verificar containers
    print('\n=== VERIFICANDO CONTAINERS ===')
    stdin, stdout, stderr = ssh.exec_command('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"')
    containers = stdout.read().decode()
    print(containers)
    
    # Testar conectividade do backend
    print('\n=== TESTANDO BACKEND LOCALMENTE ===')
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/health')
    health = stdout.read().decode()
    print(f'Health check: {health}')
    
    # Testar conectividade externa
    print('\n=== TESTANDO CONECTIVIDADE EXTERNA ===')
    stdin, stdout, stderr = ssh.exec_command('curl -s -I https://laudoesg.com')
    response = stdout.read().decode()
    print(f'Resposta do nginx: {response[:200]}')
    
    ssh.close()
    print('\n[✓] Conexão encerrada!')
    
except Exception as e:
    print(f'[✗] Erro de conexão: {e}')
    import traceback
    traceback.print_exc()