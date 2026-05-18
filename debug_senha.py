#!/usr/bin/env python3
"""Debug hash de senha no banco de dados"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Verificar o hash da senha no banco de dados
print('=== VERIFICANDO HASH DA SENHA NO BANCO ===')
cmd = 'docker exec -i eureka_db psql -U eureka -d eureka_db -c "SELECT email, senha_hash, nome FROM usuarios WHERE email = \'agapenegociosdigitais@gmail.com\';"'
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Verificar se há outros usuários
print('\n=== TODOS OS USUÁRIOS ===')
cmd = 'docker exec -i eureka_db psql -U eureka -d eureka_db -c "SELECT id, email, nome, perfil FROM usuarios;"'
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

ssh.close()