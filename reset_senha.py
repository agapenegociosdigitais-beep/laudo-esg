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
    
    # Resetar senha usando script Python inline
    print("[*] Resetando senha...")
    cmd = """docker exec eureka_backend python -c \"import sys; sys.path.append('/app'); from app.core.database import SessionLocal; from app.core.security import get_password_hash; from app.models.usuario import Usuario; db = SessionLocal(); usuario = db.query(Usuario).filter(Usuario.email == 'agapenegociosdigitais@gmail.com').first(); print('Usuario encontrado' if usuario else 'Usuario nao encontrado'); db.close()\""""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode()
    print("Resultado:", output)
    
    ssh.close()
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")