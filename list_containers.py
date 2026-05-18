#!/usr/bin/env python3
"""Listar containers Docker na VPS"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Listar todos os containers
print('=== CONTAINERS EM EXECUÇÃO ===')
stdin, stdout, stderr = ssh.exec_command('docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"')
containers = stdout.read().decode()
print(containers)

# Listar todos os containers (incluindo parados)
print('\n=== TODOS OS CONTAINERS ===')
stdin, stdout, stderr = ssh.exec_command('docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"')
all_containers = stdout.read().decode()
print(all_containers)

ssh.close()