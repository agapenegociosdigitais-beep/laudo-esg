#!/usr/bin/env python3
"""Corrigir hash bcrypt usando arquivo Python copiado para o container postgres"""
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

# Criar script Python completo no host
script_content = f"""#!/usr/bin/env python3
import psycopg2

# Hash bcrypt completo (hardcoded no script)
NOVO_HASH = "{novo_hash}"
EMAIL = "agapenegociosdigitais@gmail.com"

print(f"Hash a ser aplicado: {{NOVO_HASH}}")
print(f"Tamanho do hash: {{len(NOVO_HASH)}}")

# Conectar ao PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="eureka_db",
    user="eureka",
    password="eureka123"
)
cur = conn.cursor()

# Atualizar o hash
cur.execute(
    "UPDATE usuarios SET senha_hash = %s WHERE email = %s",
    (NOVO_HASH, EMAIL)
)

print(f"Linhas atualizadas: {{cur.rowcount}}")

# Verificar o resultado
cur.execute(
    "SELECT email, senha_hash FROM usuarios WHERE email = %s",
    (EMAIL,)
)
result = cur.fetchone()
if result:
    print(f"Email: {{result[0]}}")
    print(f"Hash salvo: {{result[1]}}")
    print(f"Tamanho do hash salvo: {{len(result[1])}}")
    print(f"Hash está completo: {{len(result[1]) == 60}}")
    print(f"Hash correto: {{result[1] == NOVO_HASH}}")

conn.commit()
cur.close()
conn.close()
print("Script concluído com sucesso!")
"""

# Salvar script no host
print("\n[*] Salvando script Python no host...")
cmd = f"cat > /tmp/fix_hash_postgres.py << 'ENDOFFILE'\n{script_content}\nENDOFFILE"
stdin, stdout, stderr = ssh.exec_command(cmd)
error = stderr.read().decode()
if error:
    print(f"[!] Erro ao salvar script: {error}")
else:
    print("[✓] Script salvo no host!")

# Copiar script para o container postgres
print("\n[*] Copiando script para o container postgres...")
cmd = "docker cp /tmp/fix_hash_postgres.py eureka_postgres:/tmp/fix_hash_postgres.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
error = stderr.read().decode()
if error:
    print(f"[!] Erro ao copiar: {error}")
else:
    print("[✓] Script copiado para o container!")

# Executar script dentro do container postgres
print("\n[*] Executando script no container postgres...")
cmd = "docker exec -i eureka_postgres python3 /tmp/fix_hash_postgres.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
error = stderr.read().decode()

if error:
    print(f"[!] Erro na execução: {error}")
else:
    print("[✓] Script executado com sucesso!")
    print(result)

# Limpar arquivos temporários
ssh.exec_command("rm /tmp/fix_hash_postgres.py")
ssh.exec_command("docker exec eureka_postgres rm /tmp/fix_hash_postgres.py")

# Verificar resultado final
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