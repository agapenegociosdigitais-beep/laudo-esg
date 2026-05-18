#!/usr/bin/env python3
"""Corrigir senha do usuário de forma simples"""
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
    
    print("[*] Atualizando senha...")
    
    # Usar Python no container PostgreSQL para evitar problemas de escaping
    python_cmd = f"""python -c \"import psycopg2; conn = psycopg2.connect(host='localhost', database='eureka_db', user='eureka'); cur = conn.cursor(); cur.execute(\"UPDATE usuarios SET senha_hash='{senha_hash}' WHERE email='agapenegociosdigitais@gmail.com';\"); conn.commit(); print('Atualizado:', cur.rowcount); cur.close(); conn.close()\""""
    
    cmd = f"docker exec eureka_postgres {python_cmd}"
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    print("Resultado:", result)
    if error:
        print("Erro:", error)
    
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