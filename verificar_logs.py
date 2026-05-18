#!/usr/bin/env python3
"""Verificar logs do backend"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

print('=== ÚLTIMOS LOGS DO BACKEND ===')
stdin, stdout, stderr = ssh.exec_command('docker logs --tail 30 eureka_backend 2>&1')
logs = stdout.read().decode()
print(logs)

ssh.close()