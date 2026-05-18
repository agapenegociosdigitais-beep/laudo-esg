#!/usr/bin/env python3
"""Corrigir hash bcrypt usando variáveis de ambiente do Docker"""
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

# Usar variável de ambiente para passar o hash sem problemas de caracteres especiais
print("\n[*] Atualizando hash usando variável de ambiente...")

# Criar um script SQL temporário com o hash completo
sql_script = f"""UPDATE usuarios SET senha_hash = '{novo_hash}' WHERE email = 'agapenegociosdigitais@gmail.com';
SELECT email, senha_hash FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';"""

# Salvar o script SQL em um arquivo temporário no host
cmd = f"echo \"{sql_script}\" > /tmp/update_senha.sql"
stdin, stdout, stderr = ssh.exec_command(cmd)

# Copiar o arquivo SQL para dentro do container postgres
cmd = "docker cp /tmp/update_senha.sql eureka_postgres:/tmp/update_senha.sql"
stdin, stdout, stderr = ssh.exec_command(cmd)

# Executar o script SQL dentro do container postgres
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -f /tmp/update_senha.sql"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error and 'UPDATE' not in error and 'SELECT' not in error:
    print(f"[!] Erro: {error}")
else:
    print(f"[✓] Script SQL executado com sucesso!")
    print(result)

# Limpar arquivos temporários
ssh.exec_command("rm /tmp/update_senha.sql")
ssh.exec_command("docker exec eureka_postgres rm /tmp/update_senha.sql")

# Verificar novamente o hash
print("\n=== VERIFICANDO RESULTADO FINAL ===")
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