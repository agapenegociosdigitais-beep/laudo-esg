#!/usr/bin/env python3
"""Criar novo usuário admin com as credenciais fornecidas"""
import paramiko
import json

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

# Dados do novo usuário admin
email = "agapenegociosdigitais@gmail.com"
senha = "sr 77840000"
nome = "Administrador Agape"
empresa = "Agape Negócios Digitais"
perfil = "admin"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Verificar se o usuário existe
    print("[*] Verificando se o usuário existe...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cd /root/eureka-terra && docker exec eureka_postgres psql -U eureka -d eureka_db -c \"SELECT id, email, nome, perfil, ativo FROM usuarios WHERE email='{email}';\"",
        timeout=10
    )
    result = stdout.read().decode()
    print(result)
    
    if email in result:
        print("\n[!] Usuário já existe. Atualizando senha...")
        # Atualizar senha do usuário existente
        stdin, stdout, stderr = ssh.exec_command(
            f"cd /root/eureka-terra && docker exec eureka_backend python -c \"\nimport sys\nsys.path.append('/app')\nfrom app.core.security import get_password_hash\nprint(get_password_hash('{senha}'))\n\"",
            timeout=10
        )
        password_hash = stdout.read().decode().strip()
        
        if password_hash:
            print(f"Hash gerado: {password_hash[:50]}...")
            
            # Atualizar no banco
            update_cmd = f"docker exec eureka_postgres psql -U eureka -d eureka_db -c \"UPDATE usuarios SET senha_hash='{password_hash}', nome='{nome}', empresa='{empresa}', perfil='{perfil}', ativo=true WHERE email='{email}';\""
            
            stdin, stdout, stderr = ssh.exec_command(update_cmd, timeout=10)
            update_result = stdout.read().decode()
            print("\nResultado da atualização:")
            print(update_result)
            
            # Verificar se atualizou
            stdin, stdout, stderr = ssh.exec_command(
                f"docker exec eureka_postgres psql -U eureka -d eureka_db -c \"SELECT id, email, nome, perfil, ativo FROM usuarios WHERE email='{email}';\"",
                timeout=10
            )
            verify_result = stdout.read().decode()
            print("\nUsuário após atualização:")
            print(verify_result)
            
            print("\n✅ SENHA ATUALIZADA COM SUCESSO!")
        else:
            print("❌ Erro ao gerar hash da senha")
    else:
        print("\n[!] Usuário não encontrado. Criando novo usuário...")
        # Criar novo usuário
        payload = {
            "email": email,
            "senha": senha,
            "nome": nome,
            "empresa": empresa,
            "perfil": perfil
        }
        
        json_payload = json.dumps(payload)
        cmd = f"""curl -s -X POST http://localhost:8000/api/v1/auth/registrar \\
  -H "Content-Type: application/json" \\
  -d '{json_payload}'"""
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        result = stdout.read().decode()
        
        print("\nResultado:")
        print(result)
    
    ssh.close()
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")