#!/usr/bin/env python3
"""Corrigir hash bcrypt usando conexão direta ao PostgreSQL"""
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

# Criar script Python para executar no servidor
script_content = f"""
import psycopg2
import bcrypt

# Conectar ao PostgreSQL
conn = psycopg2.connect(
    host="eureka_postgres",
    database="eureka_db",
    user="eureka",
    password="eureka123"
)
cur = conn.cursor()

# Atualizar o hash
novo_hash = '{novo_hash}'
email = 'agapenegociosdigitais@gmail.com'

cur.execute(
    "UPDATE usuarios SET senha_hash = %s WHERE email = %s",
    (novo_hash, email)
)

print(f"Linhas atualizadas: {{cur.rowcount}}")

# Verificar o resultado
cur.execute(
    "SELECT email, senha_hash FROM usuarios WHERE email = %s",
    (email,)
)
result = cur.fetchone()
if result:
    print(f"Email: {{result[0]}}")
    print(f"Hash salvo: {{result[1]}}")
    print(f"Tamanho do hash salvo: {{len(result[1])}} caracteres")

conn.commit()
cur.close()
conn.close()
"""

# Salvar script no servidor remoto
print(f"\n[*] Salvando script no servidor...")
cmd = f"cat > /tmp/fix_hash.py << 'EOF'\n{script_content}\nEOF"
stdin, stdout, stderr = ssh.exec_command(cmd)
error = stderr.read().decode()
if error:
    print(f"[!] Erro ao salvar script: {error}")
else:
    print("[✓] Script salvo com sucesso!")

# Executar script dentro do container backend (que tem psycopg2)
print(f"\n[*] Executando script no container backend...")
cmd = "docker exec -i eureka_backend python /tmp/fix_hash.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error:
    print(f"[!] Erro na execução: {error}")
else:
    print("[✓] Script executado com sucesso!")
    print(result)

# Limpar arquivo temporário
ssh.exec_command("rm /tmp/fix_hash.py")

ssh.close()

print(f"\n{'='*60}")
print("✅ CORREÇÃO APLICADA!")
print(f"{'='*60}")
print("Usuário: agapenegociosdigitais@gmail.com")
print(f"Nova senha: {nova_senha}")
print(f"Hash completo: {novo_hash}")
print("\nTeste o login agora!")
print(f"{'='*60}")