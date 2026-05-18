#!/usr/bin/env python3
"""
Teste para verificar se as APIs estão retornando dados reais ou simulados
"""
import sys
import json
import requests
from datetime import datetime

def test_api_real_vs_simulado():
    """Testa as APIs para identificar se retornam dados reais ou simulados"""
    
    print("=" * 80)
    print("ANÁLISE DE APIS - DADOS REAIS vs SIMULADOS")
    print("=" * 80)
    
    # Testar endpoint de busca CAR
    print("\n[1] Testando endpoint /api/v1/propriedades/buscar-car")
    print("-" * 80)
    
    # Testar com um CAR real do Pará (SEMAS-PA)
    car_teste = "PA-1506807-7B4C7F0A3D2E1B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4"
    
    try:
        response = requests.post(
            'https://laudoesg.com/api/v1/propriedades/buscar-car',
            json={"numero_car": car_teste},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Requisição bem-sucedida (Status: {response.status_code})")
            print(f"\nDados retornados:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Analisar fonte dos dados
            fonte = data.get('fonte', 'Não especificada')
            encontrado = data.get('encontrado', False)
            
            print(f"\n📊 ANÁLISE:")
            print(f"   - Fonte declarada: {fonte}")
            print(f"   - CAR encontrado: {'Sim' if encontrado else 'Não'}")
            
            if 'simulado' in fonte.lower() or 'mock' in fonte.lower():
                print("   ⚠️  DADOS SIMULADOS detectados!")
            elif 'sicar' in fonte.lower() or 'semas' in fonte.lower():
                print("   ✅ DADOS REAIS detectados!")
            else:
                print("   ❓ Fonte não identificada claramente")
                
            # Verificar se tem geometria real
            geojson = data.get('geojson')
            if geojson and geojson.get('features'):
                print("   ✅ Geometria GeoJSON presente")
            else:
                print("   ⚠️  Sem geometria GeoJSON")
                
        else:
            print(f"✗ Erro na requisição (Status: {response.status_code})")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"✗ Erro ao testar: {e}")
    
    # Testar endpoint de análise
    print("\n\n[2] Testando endpoint /api/v1/analises/iniciar")
    print("-" * 80)
    
    try:
        # Primeiro fazer login para obter token
        print("[*] Fazendo login para obter token...")
        login_response = requests.post(
            'https://laudoesg.com/api/v1/auth/login',
            json={
                "email": "agapenegociosdigitais@gmail.com",
                "password": "Admin@123456"
            },
            timeout=30
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('access_token')
            print(f"✓ Login bem-sucedido, token obtido")
            
            # Testar análise com um CAR
            print("\n[*] Iniciando análise de conformidade...")
            headers = {"Authorization": f"Bearer {token}"}
            
            analise_response = requests.post(
                'https://laudoesg.com/api/v1/analises/iniciar',
                headers=headers,
                json={
                    "numero_car": car_teste,
                    "nome_propriedade": "Teste Análise"
                },
                timeout=60
            )
            
            if analise_response.status_code in [200, 201]:
                analise_data = analise_response.json()
                print(f"✓ Análise iniciada com sucesso")
                print(f"\nDados da análise:")
                print(json.dumps(analise_data, indent=2, ensure_ascii=False))
                
                # Analisar fontes dos dados
                print(f"\n📊 ANÁLISE DE FONTES:")
                
                # Verificar desmatamento
                desmatamento = analise_data.get('desmatamento', {})
                if desmatamento:
                    fonte_dm = desmatamento.get('fonte', 'Não especificada')
                    print(f"   - Desmatamento: {fonte_dm}")
                    if 'simulado' in fonte_dm.lower():
                        print("     ⚠️  Dados SIMULADOS")
                    elif 'prodes' in fonte_dm.lower() or 'terrabrasilis' in fonte_dm.lower():
                        print("     ✅ Dados REAIS do PRODES/INPE")
                
                # Verificar áreas protegidas
                areas_protegidas = analise_data.get('areas_protegidas', {})
                for key, area in areas_protegidas.items():
                    if isinstance(area, dict):
                        fonte_area = area.get('fonte', 'Não especificada')
                        print(f"   - {key}: {fonte_area}")
                
                # Verificar embargos
                embargos = analise_data.get('embargos', {})
                for orgao, embargo in embargos.items():
                    if isinstance(embargo, dict):
                        fonte_emb = embargo.get('fonte', 'Não especificada')
                        print(f"   - Embargo {orgao}: {fonte_emb}")
                        
            else:
                print(f"✗ Erro ao iniciar análise (Status: {analise_response.status_code})")
                print(f"Resposta: {analise_response.text}")
        else:
            print(f"✗ Erro no login (Status: {login_response.status_code})")
            
    except Exception as e:
        print(f"✗ Erro ao testar análise: {e}")
    
    # Testar APIs externas diretamente
    print("\n\n[3] Testando APIs externas diretamente")
    print("-" * 80)
    
    apis_teste = [
        {
            "nome": "SICAR Nacional (GeoServer)",
            "url": "https://geoserver.car.gov.br/geoserver/sicar/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=sicar:sicar_imoveis_pa&CQL_FILTER=cod_imovel='PA-1506807-7B4C7F0A3D2E1B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4'&outputFormat=application/json",
            "esperado": 200
        },
        {
            "nome": "TerraBrasilis PRODES",
            "url": "https://terrabrasilis.dpi.inpe.br/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=prodes-legal-amz:yearly_deforestation&outputFormat=application/json&count=1",
            "esperado": 200
        },
        {
            "nome": "SEMAS-PA GeoServer",
            "url": "https://car.semas.pa.gov.br/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=semas:car_validado_semas_pa&CQL_FILTER=numero_car='PA-1506807-7B4C7F0A3D2E1B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4'&outputFormat=application/json",
            "esperado": 200
        }
    ]
    
    for api in apis_teste:
        print(f"\n[*] Testando {api['nome']}...")
        try:
            resp = requests.get(api['url'], timeout=30)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == api['esperado']:
                data = resp.json()
                if 'features' in data:
                    features = data['features']
                    print(f"   ✅ API acessível - {len(features)} features encontradas")
                    if len(features) > 0:
                        print(f"   ✅ DADOS REAIS disponíveis")
                    else:
                        print(f"   ⚠️  API acessível mas sem dados para este CAR")
                else:
                    print(f"   ⚠️  Resposta inesperada da API")
            else:
                print(f"   ❌ Erro ao acessar API")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 80)
    print("ANÁLISE CONCLUÍDA")
    print("=" * 80)

if __name__ == "__main__":
    test_api_real_vs_simulado()
