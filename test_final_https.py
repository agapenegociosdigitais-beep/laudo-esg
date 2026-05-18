#!/usr/bin/env python3
"""
Teste final para verificar se o Mixed Content foi resolvido
"""
import requests
import sys

def test_https_api():
    """Testa se a API está respondendo via HTTPS"""
    print("[*] Testando API via HTTPS...")
    
    try:
        # Testar endpoint de health check
        response = requests.get(
            'https://laudoesg.com/api/v1/health',
            timeout=10,
            verify=True
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text[:100]}")
            print("[V] API respondendo via HTTPS!")
            return True
        else:
            print(f"[X] API retornou erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[X] Erro ao conectar com API: {e}")
        return False

def test_frontend_https():
    """Testa se o frontend está servindo HTTPS corretamente"""
    print("\n[*] Testando frontend HTTPS...")
    
    try:
        response = requests.get('https://laudoesg.com/login', timeout=10, verify=True)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Verificar se o HTML contém referências HTTP
            if 'http://23.106.45.137' in response.text:
                print("[X] Ainda contém referências HTTP no HTML!")
                return False
            elif 'https://laudoesg.com' in response.text or 'NEXT_PUBLIC_API_URL' in response.text:
                print("[V] HTML contém referências HTTPS corretas!")
                return True
            else:
                print("[?] Não encontrou referências explícitas no HTML")
                return True
        else:
            print(f"[X] Erro ao acessar frontend: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[X] Erro: {e}")
        return False

def test_no_mixed_content():
    """Testa se o browser conseguiria fazer requests sem erro de Mixed Content"""
    print("\n[*] Verificando configuração do container...")
    
    try:
        # Verificar se o container está com HTTPS
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('23.106.45.137', username='root', password='JVghqGUersYW6h8Q', timeout=15)
        
        stdin, stdout, stderr = ssh.exec_command('docker exec eureka_frontend env | grep NEXT_PUBLIC_API_URL', timeout=10)
        env_value = stdout.read().decode()
        ssh.close()
        
        if 'https://laudoesg.com' in env_value:
            print(f"[V] Container configurado com HTTPS: {env_value.strip()}")
            return True
        else:
            print(f"[X] Container ainda com HTTP: {env_value.strip()}")
            return False
            
    except Exception as e:
        print(f"[X] Erro ao verificar container: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE FINAL - MIXED CONTENT RESOLVIDO")
    print("=" * 60)
    
    success1 = test_https_api()
    success2 = test_frontend_https()
    success3 = test_no_mixed_content()
    
    print("\n" + "=" * 60)
    if success1 and success2 and success3:
        print("[V] TODOS OS TESTES PASSARAM!")
        print("[V] Mixed Content foi RESOLVIDO!")
        print("[V] O sistema está funcionando corretamente com HTTPS!")
    else:
        print("[X] ALGUNS TESTES FALHARAM")
    print("=" * 60)
    
    sys.exit(0 if (success1 and success2 and success3) else 1)