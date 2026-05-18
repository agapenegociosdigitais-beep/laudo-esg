#!/usr/bin/env python3
"""Resetar senha do usuário agapenegociosdigitais@gmail.com"""
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
    
    # Hash da senha 'sr 77840000' gerada com bcrypt
    senha_hash = "$2b$12$gWD.BPOpVgFU4m9IyPKguuqzJxuibiPbfdcj6Ko.lQ5NYuAZ95iAG"
    
    # Atualizar senha via SQL
    print("[*] Atualizando senha no PostgreSQL...")
    sql = f"UPDATE usuarios SET senha_hash='{senha_hash}', nome='Administrador Agape', empresa='Agape Negócios Digitais', perfil='admin', ativo=true WHERE email='agapenegociosdigitais@gmail.com';"
    
    cmd = f"docker exec eureka_postgres psql -U eureka -d eureka_db -c \"{sql}\""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    print(result)
    
    # Testar login
    print("\n[*] Testando login...")
    test_cmd = "curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\": \"agapenegociosdigitais@gmail.com\", \"senha\": \"sr 77840000\"}'"
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