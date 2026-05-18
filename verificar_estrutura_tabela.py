#!/usr/bin/env python3
"""Verificar estrutura da tabela usuarios"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Verificar estrutura da tabela
print('=== ESTRUTURA DA TABELA USUARIOS ===')
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"\\d usuarios\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Verificar tipo específico do campo senha_hash
print('\n=== TIPO DO CAMPO senha_hash ===')
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'usuarios' AND column_name = 'senha_hash';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

ssh.close()