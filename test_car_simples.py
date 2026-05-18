#!/usr/bin/env python3
"""Testar CAR específico sem complicações"""
import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    print("=" * 80)
    print("TESTANDO CAR: PA-1505650-7F377A59466D4361A95386AEEEDD9BA5")
    print("=" * 80)
    
    # Login
    print("\n[1] Login...")
    try:
        r = requests.post(
            'https://laudoesg.com/api/v1/auth/login',
            json={"email": "agapenegociosdigitais@gmail.com", "senha": "Admin@123456"},
            verify=False,
            timeout=30
        )
        
        if r.status_code != 200:
            print(f"Erro login: {r.status_code}")
            print(r.text)
            return
            
        token = r.json()['access_token']
        print("✅ Login OK")
        
    except Exception as e:
        print(f"Erro: {e}")
        return
    
    # Buscar CAR
    print("\n[2] Buscando CAR...")
    car = "PA-1505650-7F377A59466D4361A95386AEEEDD9BA5"
    
    try:
        r = requests.post(
            'https://laudoesg.com/api/v1/propriedades/buscar-car',
            headers={"Authorization": f"Bearer {token}"},
            json={"numero_car": car},
            verify=False,
            timeout=30
        )
        
        print(f"Status: {r.status_code}")
        print()
        
        if r.status_code == 200:
            data = r.json()
            print("✅ DADOS RETORNADOS:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Análise
            fonte = data.get('fonte', '').lower()
            if 'simulado' in fonte:
                print("\n❌ DADOS SIMULADOS!")
            elif 'sicar' in fonte or 'semas' in fonte:
                print("\n✅ DADOS REAIS!")
            else:
                print(f"\n? Fonte: {data.get('fonte')}")
                
        elif r.status_code == 500:
            print("❌ ERRO (sem simulação):")
            print(r.json().get('detail'))
        else:
            print(f"Erro inesperado: {r.text}")
            
    except Exception as e:
        print(f"Erro ao buscar CAR: {e}")

if __name__ == "__main__":
    main()
