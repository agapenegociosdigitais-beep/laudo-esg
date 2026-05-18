#!/usr/bin/env python3
"""Testar login após atualização da senha"""
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
    
    # Testar login
    print("[*] Testando login...")
    cmd = """curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "agapenegociosdigitais@gmail.com", "senha": "77840000"}'"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    
    print("=== RESULTADO DO LOGIN ===")
    print(result)
    
    if "access_token" in result:
        print("\n✅ LOGIN BEM-SUCEDIDO!")
        print("O usuário agora pode fazer login no sistema.")
    elif "detail" in result:
        print(f"\n❌ Erro: {result}")
    else:
        print(f"\n❌ Resposta inesperada: {result[:200]}")
    
    # Verificar logs
    print("\n[*] Verificando logs do backend...")
    stdin, stdout, stderr = ssh.exec_command("docker logs eureka_backend --tail=10 2>&1", timeout=10)
    logs = stdout.read().decode()
    print("Logs recentes:")
    for line in logs.split('\n')[-5:]:
        print(line)
    
    ssh.close()
    print("\n[✓] Teste concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")