#!/usr/bin/env python3
"""Corrigir hash bcrypt diretamente no PostgreSQL - abordagem direta"""
import paramiko
import bcrypt

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

# Gerar novo hash bcrypt válido
nova_senha = 'Eureka@2024!'
senha_bytes = nova_senha.encode('utf-8')
novo_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt(12)).decode('utf-8')

print(f"[*] Gerando novo hash bcrypt válido...")
print(f"[*] Hash completo: {novo_hash}")
print(f"[*] Nova senha: {nova_senha}")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Atualizar diretamente com psql usando -c (comando inline)
print(f"\n[*] Atualizando hash no banco de dados...")

# Primeiro, verificar o hash atual
print("\n=== ANTES DA CORREÇÃO ===")
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, senha_hash FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Agora atualizar com o hash correto
print("\n=== APLICANDO CORREÇÃO ===")
cmd = f"docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"UPDATE usuarios SET senha_hash = '{novo_hash}' WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error and 'UPDATE' not in error:
    print(f"[!] Erro: {error}")
else:
    print(f"[✓] UPDATE executado!")
    print(result)

# Verificar se a atualização funcionou
print("\n=== DEPOIS DA CORREÇÃO ===")
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, LEFT(senha_hash, 60) as hash_preview FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

ssh.close()

print(f"\n{'='*60}")
print("✅ CORREÇÃO APLICADA!")
print(f"{'='*60}")
print("Usuário: agapenegociosdigitais@gmail.com")
print(f"Nova senha: {nova_senha}")
print(f"Hash completo: {novo_hash}")
print("\nTeste o login agora!")
print(f"{'='*60}")