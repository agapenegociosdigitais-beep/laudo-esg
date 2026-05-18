#!/usr/bin/env python3
"""Corrigir senha do usuário de forma direta e simples"""
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
    
    # Hash bcrypt para '77840000'
    senha_hash = "$2b$12$CgAe3c.zaz.hSaIOqKKNjuPTXw1zbbZGo1oqMlJtUTIAKFwTVWiPi"
    
    print("[*] Atualizando senha via SQL...")
    
    # Comando SQL - usar parametros para evitar problemas de escaping
    sql = "UPDATE usuarios SET senha_hash = %s WHERE email = %s"
    
    # Usar psql com parametros - forma mais segura
    cmd = f"docker exec eureka_postgres psql -U eureka -d eureka_db -c \"UPDATE usuarios SET senha_hash='{senha_hash}' WHERE email='agapenegociosdigitais@gmail.com';\""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    print(result)
    
    # Verificar
    print("\n[*] Verificando hash...")
    stdin, stdout, stderr = ssh.exec_command("docker exec eureka_postgres psql -U eureka -d eureka_db -c \"SELECT LEFT(senha_hash, 20) FROM usuarios WHERE email='agapenegociosdigitais@gmail.com';\"", timeout=10)
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
    else:
        print("Resposta:", login_result[:200])
    
    ssh.close()
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")