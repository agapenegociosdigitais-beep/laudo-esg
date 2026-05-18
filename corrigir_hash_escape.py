#!/usr/bin/env python3
"""Corrigir hash bcrypt escapando corretamente os caracteres $"""
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
print(f"[*] Tamanho do hash: {len(novo_hash)} caracteres")
print(f"[*] Nova senha: {nova_senha}")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Verificar hash atual
print("\n=== HASH ATUAL NO BANCO ===")
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, senha_hash FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Escapar os caracteres $ no hash para evitar interpretação pelo shell
# Substituir $ por \$
hash_escaped = novo_hash.replace('$', '\\$')
print(f"\n[*] Hash escapado: {hash_escaped}")

# Atualizar usando o hash escapado
print("\n[*] Atualizando hash com escapamento...")
cmd = f"docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"UPDATE usuarios SET senha_hash = '{hash_escaped}' WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error and 'UPDATE' not in error:
    print(f"[!] Erro: {error}")
else:
    print(f"[✓] UPDATE executado!")
    print(result)

# Verificar o resultado
print("\n=== VERIFICANDO RESULTADO ===")
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, senha_hash FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';\""
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