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
    
    # Comando para resetar senha diretamente no container
    print("[*] Resetando senha...")
    cmd = """docker exec eureka_backend python -c "
import sys
sys.path.append('/app')
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.usuario import Usuario

db = SessionLocal()
usuario = db.query(Usuario).filter(Usuario.email == 'agapenegociosdigitais@gmail.com').first()
if usuario:
    usuario.senha_hash = get_password_hash('sr 77840000')
    db.commit()
    print('Senha atualizada com sucesso')
else:
    print('Usuario nao encontrado')
db.close()
"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    print("Resultado:", output)
    if error:
        print("Erro:", error)
    
    # Testar login
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
        print("Resposta:", login_result[:200])
    
    ssh.close()
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")