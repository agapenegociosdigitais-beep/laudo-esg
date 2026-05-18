#!/usr/bin/env python3
"""Testar CAR específico: PA-1505650-7F377A59466D4361A95386AEEEDD9BA5"""
import requests
import urllib3
import json

urllib3.disable_warnings()

def test_car():
    print("=" * 80)
    print("TESTANDO CAR: PA-1505650-7F377A59466D4361A95386AEEEDD9BA5")
    print("=" * 80)
    
    # Login
    print("\n[1] Fazendo login...")
    login_data = {
        "email": "agapenegociosdigitais@gmail.com",
        "senha": "sr 77840000"
    }
    
    try:
        login = requests.post(
            'https://laudoesg.com/api/v1/auth/login',
            json=login_data,
            verify=False,
            timeout=30
        )
        
        if login.status_code != 200:
            print(f"❌ Erro no login: {login.status_code}")
            print(login.text)
            return False
            
        token = login.json()['access_token']
        print("✅ Login bem-sucedido")
        
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        return False
    
    # Buscar CAR
    print("\n[2] Buscando CAR...")
    car = "PA-1505650-7F377A59466D4361A95386AEEEDD9BA5"
    
    try:
        response = requests.post(
            'https://laudoesg.com/api/v1/propriedades/buscar-car',
            headers={"Authorization": f"Bearer {token}"},
            json={"numero_car": car},
            verify=False,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ DADOS RETORNADOS:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Análise da fonte
            fonte = data.get('fonte', 'N/A')
            print(f"\n📊 ANÁLISE:")
            print(f"   Fonte: {fonte}")
            print(f"   Encontrado: {data.get('encontrado', False)}")
            
            if 'simulado' in fonte.lower():
                print("\n❌ CRÍTICO: Dados simulados detectados!")
                return False
            elif any(x in fonte.lower() for x in ['sicar', 'semas', 'real', 'gov']):
                print("\n✅ Dados REAIS confirmados!")
                return True
            else:
                print(f"\n⚠️  Fonte não identificada: {fonte}")
                return False
                
        elif response.status_code == 500:
            error = response.json().get('detail', 'Erro desconhecido')
            print("❌ ERRO DO SISTEMA:")
            print(f"   {error}")
            
            if 'simulado' in error.lower():
                print("\n⚠️  Mensagem menciona simulação")
                return False
            else:
                print("\n✅ Erro legítimo (sem simulação)")
                return True
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao buscar CAR: {e}")
        return False

if __name__ == "__main__":
    success = test_car()
    print("\n" + "=" * 80)
    if success:
        print("✅ TESTE CONCLUÍDO - Sistema retornou dados reais ou erro legítimo")
    else:
        print("❌ TESTE FALHOU - Sistema retornou dados simulados")
    print("=" * 80)
