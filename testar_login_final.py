#!/usr/bin/env python3
"""Testar login após correção do hash bcrypt"""
import paramiko
import json

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Testar login via curl direto no servidor
print('=== TESTANDO LOGIN NA VPS ===')
login_data = '{"email": "agapenegociosdigitais@gmail.com", "senha": "Eureka@2024!"}'
cmd = f"curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{login_data}'"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Ver logs do backend para confirmar sucesso
print('\n=== LOGS RECENTES DO BACKEND ===')
stdin, stdout, stderr = ssh.exec_command('docker logs --tail 20 eureka_backend 2>&1')
logs = stdout.read().decode()
print(logs)

ssh.close()

# Parse do resultado
if result:
    try:
        response = json.loads(result)
        if 'access_token' in response:
            print('\n✅ LOGIN FUNCIONANDO! Token gerado com sucesso.')
        elif 'detail' in response:
            print(f'\n❌ Erro no login: {response["detail"]}')
        else:
            print(f'\n⚠️ Resposta inesperada: {response}')
    except:
        print(f'\n📄 Resposta bruta: {result}')
else:
    print('\n❌ Sem resposta do servidor')