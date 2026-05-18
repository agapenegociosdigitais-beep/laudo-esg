#!/usr/bin/env python3
"""Registrar novo usuário na VPS"""
import paramiko
import json

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

# Dados do usuário a registrar
email = "agapenegociosdigitais@gmail.com"
senha = "sr 77840000"
nome = "Administrador"
empresa = "Agape Negócios Digitais"
perfil = "admin"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Preparar dados JSON
    payload = {
        "email": email,
        "senha": senha,
        "nome": nome,
        "empresa": empresa,
        "perfil": perfil
    }
    
    # Fazer requisição de registro
    print("=== REGISTRANDO USUÁRIO ===")
    print(f"Email: {email}")
    print(f"Nome: {nome}")
    print(f"Empresa: {empresa}")
    print(f"Perfil: {perfil}")
    
    # Usar curl para fazer o POST
    json_payload = json.dumps(payload)
    cmd = f"""curl -s -X POST http://localhost:8000/api/v1/auth/registrar \\
  -H "Content-Type: application/json" \\
  -d '{json_payload}'"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    if result:
        print("\n=== RESPOSTA DO SERVIDOR ===")
        try:
            response_data = json.loads(result)
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # Verificar se foi sucesso
            if "usuario" in response_data:
                print("\n✅ USUÁRIO REGISTRADO COM SUCESSO!")
                print(f"ID: {response_data['usuario'].get('id', 'N/A')}")
                print(f"Email: {response_data['usuario'].get('email', 'N/A')}")
                print(f"Status: {'Ativo' if response_data['usuario'].get('ativo') else 'Inativo'}")
            elif "detail" in response_data:
                print(f"\n❌ ERRO: {response_data['detail']}")
            else:
                print(f"\n❌ ERRO DESCONHECIDO: {result}")
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
    print("\n[✓] Processo concluído!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")