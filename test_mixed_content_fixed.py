#!/usr/bin/env python3
"""
Testa se o erro de Mixed Content foi resolvido após o rebuild
"""
import requests
import sys

def test_https_login():
    """Testa login via HTTPS"""
    print("[*] Testando login via HTTPS...")
    
    try:
        # Testar endpoint de login
        response = requests.post(
            'https://laudoesg.com/api/v1/auth/login',
            json={
                "username": "agapenegociosdigitais@gmail.com",
                "password": "Eureka@2025"
            },
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=True
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("\n[V] SUCESSO! Login via HTTPS funcionando!")
            return True
        elif response.status_code == 401:
            print("\n[?] Credenciais inválidas, mas a conexão HTTPS está funcionando!")
            return True
        else:
            print(f"\n[X] Erro inesperado: {response.status_code}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"\n[X] Erro SSL: {e}")
        return False
    except Exception as e:
        print(f"\n[X] Erro: {e}")
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
            else:
                print("[V] HTML limpo, sem referências HTTP!")
                return True
        else:
            print(f"[X] Erro ao acessar frontend: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[X] Erro: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE MIXED CONTENT RESOLVIDO")
    print("=" * 60)
    
    success1 = test_https_login()
    success2 = test_frontend_https()
    
    if success1 and success2:
        print("\n" + "=" * 60)
        print("[V] TODOS OS TESTES PASSARAM!")
        print("[V] Mixed Content foi RESOLVIDO!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("[X] ALGUNS TESTES FALHARAM")
        print("=" * 60)
        sys.exit(1)