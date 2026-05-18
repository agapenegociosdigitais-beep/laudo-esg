#!/usr/bin/env python3
"""Corrigir hash bcrypt usando abordagem simples com heredoc"""
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

# Usar heredoc para criar e executar script Python dentro do container
print("\n[*] Criando e executando script dentro do container...")

# Comando para criar e executar script diretamente no container
script_cmd = f"""docker exec -i eureka_backend python -c "
import psycopg2
import bcrypt

# Conectar ao PostgreSQL
conn = psycopg2.connect(
    host='eureka_postgres',
    database='eureka_db',
    user='eureka',
    password='eureka123'
)
cur = conn.cursor()

# Atualizar o hash
novo_hash = '{novo_hash}'
email = 'agapenegociosdigitais@gmail.com'

cur.execute(
    'UPDATE usuarios SET senha_hash = %s WHERE email = %s',
    (novo_hash, email)
)

print(f'Linhas atualizadas: {{cur.rowcount}}')

# Verificar o resultado
cur.execute(
    'SELECT email, senha_hash FROM usuarios WHERE email = %s',
    (email,)
)
result = cur.fetchone()
if result:
    print(f'Email: {{result[0]}}')
    print(f'Hash salvo: {{result[1]}}')
    print(f'Tamanho do hash salvo: {{len(result[1])}} caracteres')

conn.commit()
cur.close()
conn.close()
"
"""

stdin, stdout, stderr = ssh.exec_command(script_cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error:
    print(f"[!] Erro na execução: {error}")
else:
    print("[✓] Script executado com sucesso!")
    print(result)

# Verificar novamente o hash
print("\n=== VERIFICANDO RESULTADO FINAL ===")
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