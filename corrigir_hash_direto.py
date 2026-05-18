#!/usr/bin/env python3
"""Corrigir hash bcrypt diretamente no PostgreSQL"""
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

# Usar psql diretamente com o hash completo
print(f"\n[*] Atualizando hash no banco de dados...")

# Criar arquivo SQL temporário com o hash completo
sql_content = f"""UPDATE usuarios SET senha_hash = '{novo_hash}' WHERE email = 'agapenegociosdigitais@gmail.com';
SELECT email, LEFT(senha_hash, 50) as hash_preview FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';
"""

# Escrever SQL em arquivo temporário no servidor
cmd = f"echo \"{sql_content}\" > /tmp/fix_senha.sql"
stdin, stdout, stderr = ssh.exec_command(cmd)

# Executar SQL no PostgreSQL
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -f /tmp/fix_senha.sql"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error and 'UPDATE' not in error and 'SELECT' not in error:
    print(f"[!] Erro: {error}")
else:
    print(f"[✓] Comando executado com sucesso!")
    print(result)

# Limpar arquivo temporário
ssh.exec_command("rm /tmp/fix_senha.sql")

ssh.close()

print(f"\n{'='*60}")
print("✅ CORREÇÃO APLICADA!")
print(f"{'='*60}")
print("Usuário: agapenegociosdigitais@gmail.com")
print(f"Nova senha: {nova_senha}")
print(f"Hash completo: {novo_hash[:60]}...")
print("\nTeste o login agora!")
print(f"{'='*60}")