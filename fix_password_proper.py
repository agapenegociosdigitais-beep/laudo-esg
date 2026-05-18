#!/usr/bin/env python3
"""Corrigir hash da senha usando arquivo SQL temporário"""
import paramiko

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Hash bcrypt correto para '77840000'
    senha_hash = "$2b$12$CgAe3c.zaz.hSaIOqKKNjuPTXw1zbbZGo1oqMlJtUTIAKFwTVWiPi"
    
    print("[*] Criando arquivo SQL temporário na VPS...")
    
    # Criar arquivo SQL com o comando UPDATE
    sql_content = f"""-- Atualizar senha do usuário agapenegociosdigitais@gmail.com
UPDATE usuarios 
SET senha_hash = '{senha_hash}'
WHERE email = 'agapenegociosdigitais@gmail.com';
"""
    
    # Salvar arquivo SQL temporário na VPS
    with open("/tmp/fix_password.sql", "w") as f:
        f.write(sql_content)
    
    # Copiar arquivo para a VPS via SFTP
    sftp = ssh.open_sftp()
    sftp.put("/tmp/fix_password.sql", "/tmp/fix_password.sql")
    sftp.close()
    
    print("[*] Executando arquivo SQL no PostgreSQL...")
    
    # Executar o arquivo SQL no container PostgreSQL
    stdin, stdout, stderr = ssh.exec_command("docker exec eureka_postgres psql -U eureka -d eureka_db -f /tmp/fix_password.sql", timeout=10)
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    print("Resultado:")
    print(result)
    if error:
        print("Erro:", error)
    
    # Limpar arquivo temporário
    ssh.exec_command("rm /tmp/fix_password.sql")
    
    # Verificar se atualizou corretamente
    print("\n[*] Verificando hash atualizado...")
    stdin, stdout, stderr = ssh.exec_command("docker exec eureka_postgres psql -U eureka -d eureka_db -c \"SELECT email, LEFT(senha_hash, 20) as hash_preview FROM usuarios WHERE email='agapenegociosdigitais@gmail.com';\"", timeout=10)
    verify = stdout.read().decode()
    print(verify)
    
    # Testar login
    print("\n[*] Testando login...")
    test_cmd = "curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\": \"agapenegociosdigitais@gmail.com\", \"senha\": \"77840000\"}'"
    stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=10)
    login_result = stdout.read().decode()
    
    print("\n=== RESULTADO DO LOGIN ===")
    if "access_token" in login_result:
        print("✅ LOGIN BEM-SUCEDIDO!")
        print("O usuário agora pode fazer login no sistema.")
    else:
        print("Resposta:", login_result[:200])
    
    ssh.close()
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")