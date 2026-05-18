#!/usr/bin/env python3
"""Debug erro 500 no endpoint buscar-car"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

print('=== VERIFICANDO ERRO 500 NO ENDPOINT BUSCAR-CAR ===')

# Ver logs recentes do backend
print('\n=== LOGS RECENTES (últimos 30 segundos) ===')
stdin, stdout, stderr = ssh.exec_command('docker logs --tail 50 eureka_backend 2>&1')
logs = stdout.read().decode()
print(logs)

# Testar o endpoint diretamente
print('\n=== TESTANDO ENDPOINT BUSCAR-CAR ===')
cmd = "docker exec eureka_backend curl -s -X POST http://localhost:8000/api/v1/propriedades/buscar-car -H 'Content-Type: application/json' -d '{\"car\": \"PA1506807\"}'"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(f'Resposta: {result}')

ssh.close()