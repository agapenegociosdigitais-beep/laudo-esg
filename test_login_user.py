#!/usr/bin/env python3
"""Testar login do usuário agapenegociosdigitais@gmail.com"""
import paramiko
import json

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

# Credenciais do usuário
email = "agapenegociosdigitais@gmail.com"
senha = "sr 77840000"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Preparar dados de login
    payload = {
        "email": email,
        "senha": senha
    }
    
    print("=== TESTANDO LOGIN ===")
    print(f"Email: {email}")
    
    # Fazer requisição de login
    json_payload = json.dumps(payload)
    cmd = f"""curl -s -X POST http://localhost:8000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{json_payload}'"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    print("\n=== RESPOSTA DO SERVIDOR ===")
    try:
        response_data = json.loads(result)
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        # Verificar se foi sucesso
        if "access_token" in response_data:
            print("\n✅ LOGIN BEM-SUCEDIDO!")
            print(f"Token: {response_data['access_token'][:50]}...")
            print(f"Tipo: {response_data['token_type']}")
            print(f"Usuário: {response_data.get('usuario', {}).get('nome', 'N/A')}")
            print(f"Perfil: {response_data.get('usuario', {}).get('perfil', 'N/A')}")
        elif "detail" in response_data:
            print(f"\n❌ ERRO DE LOGIN: {response_data['detail']}")
        else:
            print(f"\n❌ RESPOSTA INESPERADA: {result}")
    except json.JSONDecodeError:
        print("Resposta (texto):", result[:500])
    
    if error:
        print("\n=== ERRO ===")
        print(error)
    
    # Ver logs do backend
    print("\n=== LOGS DO BACKEND ===")
    stdin, stdout, stderr = ssh.exec_command('docker logs eureka_backend --tail=10', timeout=10)
    logs = stdout.read().decode()
    print(logs)
    
    ssh.close()
    print("\n[✓] Teste concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")