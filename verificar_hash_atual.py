#!/usr/bin/env python3
"""Verificar hash atual no banco de dados"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Verificar o hash atual no banco
print('=== HASH ATUAL NO BANCO ===')
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, senha_hash FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Verificar se há algum erro
error = stderr.read().decode()
if error:
    print(f'Erro: {error}')

ssh.close()