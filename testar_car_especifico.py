#!/usr/bin/env python3
"""
Testar CAR específico: PA-1505650-7F377A59466D4361A95386AEEEDD9BA5
"""
import requests
import urllib3
import json

urllib3.disable_warnings()

def testar_car():
    print("=" * 80)
    print("TESTANDO CAR ESPECÍFICO")
    print("=" * 80)
    
    # Fazer login
    print("\n[1] Fazendo login...")
    login = requests.post(
        'https://laudoesg.com/api/v1/auth/login',
        json={'email': 'agapenegociosdigitais@gmail.com', 'senha': 'Admin@123456'},
        verify=False,
        timeout=30
    )
    
    if login.status_code != 200:
        print(f"❌ Erro no login: {login.status_code}")
        print(login.text)
        return False
    
    token = login.json()['access_token']
    print("✅ Login bem-sucedido")
    
    # Testar o CAR
    car = "PA-1505650-7F377A59466D4361A95386AEEEDD9BA5"
    print(f"\n[2] Buscando CAR: {car}")
    
    response = requests.post(
        'https://laudoesg.com/api/v1/propriedades/buscar-car',
        headers={'Authorization': f'Bearer {token}'},
        json={'numero_car': car},
        verify=False,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ DADOS RETORNADOS:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Análise
        fonte = data.get('fonte', 'N/A')
        encontrado = data.get('encontrado', False)
        
        print(f"\n📊 ANÁLISE:")
        print(f"   Fonte: {fonte}")
        print(f"   Encontrado: {encontrado}")
        
        if 'simulado' in fonte.lower():
            print("\n❌ CRÍTICO: Dados simulados detectados!")
            return False
        elif any(x in fonte.lower() for x in ['sicar', 'semas', 'real', 'gov']):
            print("\n✅ Dados reais confirmados!")
            return True
        else:
            print(f"\n⚠️  Fonte não identificada: {fonte}")
            return False
            
    elif response.status_code == 500:
        data = response.json()
        error = data.get('detail', 'Erro desconhecido')
        print(f"\n❌ ERRO DO SISTEMA:")
        print(f"   {error}")
        
        if 'simulado' in error.lower():
            print("\n⚠️  Mensagem de erro menciona simulação")
            return False
        else:
            print("\n✅ Erro legítimo (sem simulação)")
            return True
    else:
        print(f"\n❌ Status inesperado: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    testar_car()
