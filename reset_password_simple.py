#!/usr/bin/env python3
"""Resetar senha do usuário usando script Python direto no backend"""
import paramiko

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

email = "agapenegociosdigitais@gmail.com"
nova_senha = "sr 77840000"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Criar script Python para resetar senha
    script = f"""
import sys
sys.path.append('/app')
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.usuario import Usuario

email = '{email}'
nova_senha = '{nova_senha}'

db = SessionLocal()
usuario = db.query(Usuario).filter(Usuario.email == email).first()

if usuario:
    usuario.senha_hash = get_password_hash(nova_senha)
    db.commit()
    print(f"✅ Senha atualizada para usuário: {{usuario.nome}} ({{email}})")
else:
    print(f"❌ Usuário não encontrado: {{email}}")

db.close()
"""
    
    # Salvar script temporário na VPS
    print("[*] Criando script de reset de senha...")
    stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/reset_senha.py << 'EOF'\n{script}\nEOF", timeout=10)
    print(stdout.read().decode())
    
    # Executar script no container backend
    print("\n[*] Executando script no backend...")
    stdin, stdout, stderr = ssh.exec_command("docker exec eureka_backend python /tmp/reset_senha.py", timeout=30)
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if output:
        print("Resultado:", output)
    if error:
        print("Erro:", error)
    
    # Limpar arquivo temporário
    print("\n[*] Limpando arquivo temporário...")
    ssh.exec_command("rm /tmp/reset_senha.py", timeout=5)
    
    # Testar login com nova senha
    print("\n[*] Testando login com nova senha...")
    test_cmd = f"""curl -s -X POST http://localhost:8000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{{"email": "{email}", "senha": "{nova_senha}"}}'"""
    
    stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=10)
    result = stdout.read().decode()
    
    print("\n=== RESULTADO DO LOGIN ===")
    if "access_token" in result:
        print("✅ LOGIN BEM-SUCEDIDO!")
        print("O usuário pode agora fazer login no sistema.")
    elif "detail" in result:
        print(f"❌ Erro: {result}")
    else:
        print(f"Resposta: {result}")
    
    ssh.close()
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")