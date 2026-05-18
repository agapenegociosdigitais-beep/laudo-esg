#!/usr/bin/env python3
"""Corrige hash de senha inválido no banco de dados"""
import paramiko
import bcrypt

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

# Gerar novo hash bcrypt válido
nova_senha = 'Eureka@2024!'  # Senha temporária
senha_bytes = nova_senha.encode('utf-8')
novo_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt(12)).decode('utf-8')

print(f"[*] Gerando novo hash bcrypt válido...")
print(f"[*] Nova senha temporária: {nova_senha}")
print(f"[*] Hash gerado: {novo_hash[:50]}...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Atualizar a senha no banco de dados
print(f"\n[*] Atualizando senha no banco de dados...")
cmd = f"docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"UPDATE usuarios SET senha_hash = '{novo_hash}' WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error and 'UPDATE' not in error:
    print(f"[!] Erro: {error}")
else:
    print(f"[✓] Senha atualizada com sucesso!")
    print(result)

# Verificar se a atualização funcionou
print(f"\n[*] Verificando atualização...")
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, nome, perfil FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

ssh.close()

print(f"\n{'='*60}")
print("✅ CORREÇÃO CONCLUÍDA!")
print(f"{'='*60}")
print("Usuário: agapenegociosdigitais@gmail.com")
print(f"Nova senha: {nova_senha}")
print("\nTeste o login agora!")
print(f"{'='*60}")