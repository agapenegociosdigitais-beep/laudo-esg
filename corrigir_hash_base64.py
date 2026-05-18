#!/usr/bin/env python3
"""Corrigir hash bcrypt usando base64 para evitar problemas com caracteres especiais"""
import paramiko
import bcrypt
import base64

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

# Codificar em base64 para evitar problemas com caracteres especiais
hash_base64 = base64.b64encode(novo_hash.encode('utf-8')).decode('utf-8')
print(f"[*] Hash em base64: {hash_base64[:50]}...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

# Verificar hash atual
print("\n=== HASH ATUAL NO BANCO ===")
cmd = "docker exec -i eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, senha_hash FROM usuarios WHERE email = 'agapenegociosdigitais@gmail.com';\""
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Usar Python dentro do container para decodificar base64 e atualizar o banco
print("\n[*] Atualizando hash usando base64...")

script_cmd = f"""docker exec -i eureka_backend python -c "
import psycopg2
import base64

# Decodificar hash do base64
hash_base64 = '{hash_base64}'
novo_hash = base64.b64decode(hash_base64).decode('utf-8')

print(f'Hash decodificado: {{novo_hash}}')
print(f'Tamanho: {{len(novo_hash)}} caracteres')

# Conectar ao PostgreSQL
conn = psycopg2.connect(
    host='eureka_postgres',
    database='eureka_db',
    user='eureka',
    password='eureka123'
)
cur = conn.cursor()

# Atualizar o hash
cur.execute(
    'UPDATE usuarios SET senha_hash = %s WHERE email = %s',
    (novo_hash, 'agapenegociosdigitais@gmail.com')
)

print(f'Linhas atualizadas: {{cur.rowcount}}')

# Verificar o resultado
cur.execute(
    'SELECT email, senha_hash FROM usuarios WHERE email = %s',
    ('agapenegociosdigitais@gmail.com',)
)
result = cur.fetchone()
if result:
    print(f'Email: {{result[0]}}')
    print(f'Hash salvo: {{result[1]}}')
    print(f'Tamanho do hash salvo: {{len(result[1])}} caracteres')
    print(f'Hash está completo: {{len(result[1]) == 60}}')

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