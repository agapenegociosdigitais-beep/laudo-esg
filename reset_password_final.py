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
    
    # Senha hash para 'sr 77840000' (gerada com bcrypt)
    senha_hash = "$2b$12$gWD.BPOpVgFU4m9IyPKguuqzJxuibiPbfdcj6Ko.lQ5NYuAZ95iAG"
    
    print("[*] Atualizando senha no banco de dados...")
    
    # Comando SQL para atualizar
    sql_cmd = f"""UPDATE usuarios SET 
        senha_hash='{senha_hash}', 
        nome='Administrador Agape', 
        empresa='Agape Negócios Digitais', 
        perfil='admin', 
        ativo=true 
    WHERE email='agapenegociosdigitais@gmail.com';"""
    
    # Executar no PostgreSQL
    cmd = f"docker exec eureka_postgres psql -U eureka -d eureka_db -c \"{sql_cmd}\""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    print("Resultado:")
    print(result)
    if error:
        print("Erro:", error)
    
    print("\n[*] Verificando usuário...")
    verify_cmd = "docker exec eureka_postgres psql -U eureka -d eureka_db -c \"SELECT id, email, nome, perfil, ativo FROM usuarios WHERE email='agapenegociosdigitais@gmail.com';\""
    stdin, stdout, stderr = ssh.exec_command(verify_cmd, timeout=10)
    verify = stdout.read().decode()
    print(verify)
    
    print("\n[*] Testando login...")
    test_cmd = """curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "agapenegociosdigitais@gmail.com", "senha": "sr 77840000"}'"""
    
    stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=10)
    login_result = stdout.read().decode()
    
    print("\n=== RESULTADO DO LOGIN ===")
    if "access_token" in login_result:
        print("✅ LOGIN BEM-SUCEDIDO!")
        print("O usuário agora pode fazer login no sistema.")
    else:
        print("Resposta:", login_result)
    
    ssh.close()
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")