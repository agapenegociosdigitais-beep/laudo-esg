#!/usr/bin/env python3
"""
Diagnóstico detalhado das APIs - Verifica se retornam dados reais ou simulados
"""
import sys
import json
import requests
import urllib3
from datetime import datetime

# Desabilitar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_login():
    """Faz login e retorna token"""
    try:
        response = requests.post(
            'https://laudoesg.com/api/v1/auth/login',
            json={
                "email": "agapenegociosdigitais@gmail.com",
                "senha": "Admin@123456"  # Note: 'senha' não 'password'
            },
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            print(f"❌ Erro no login: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        return None

def test_busca_car(token):
    """Testa busca de CAR com autenticação"""
    print("\n[1] Testando BUSCA DE CAR")
    print("-" * 80)
    
    # Testar com CARs conhecidos
    cars_teste = [
        "PA-1506807-7B4C7F0A3D2E1B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4",
        "MT-5107248-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # CAR provavelmente não existe
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for car in cars_teste:
        print(f"\n[*] Testando CAR: {car[:30]}...")
        try:
            response = requests.post(
                'https://laudoesg.com/api/v1/propriedades/buscar-car',
                headers=headers,
                json={"numero_car": car},
                timeout=30,
                verify=False
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                fonte = data.get('fonte', 'Não especificada')
                encontrado = data.get('encontrado', False)
                
                print(f"   Fonte: {fonte}")
                print(f"   Encontrado: {'Sim' if encontrado else 'Não'}")
                
                if encontrado:
                    print(f"   Nome: {data.get('nome_propriedade', 'N/A')}")
                    print(f"   Área: {data.get('area_ha', 'N/A')} ha")
                    print(f"   Município: {data.get('municipio', 'N/A')}")
                    print(f"   Status: {data.get('status_car', 'N/A')}")
                    
                    # Verificar se é simulado
                    if any(x in fonte.lower() for x in ['simulado', 'mock', 'fake', 'exemplo']):
                        print("   ⚠️  ⚠️  ⚠️  DADOS SIMULADOS DETECTADOS!")
                    elif any(x in fonte.lower() for x in ['sicar', 'semas', 'real', 'gov', 'br']):
                        print("   ✅ DADOS REAIS CONFIRMADOS!")
                    else:
                        print("   ❓ Fonte não identificada")
                else:
                    print("   ⚠️  CAR não encontrado nas bases")
                    
            else:
                print(f"   Erro: {response.text}")
                
        except Exception as e:
            print(f"   Erro: {e}")

def test_analise_completa(token):
    """Testa análise completa de conformidade"""
    print("\n\n[2] Testando ANÁLISE DE CONFORMIDADE COMPLETA")
    print("-" * 80)
    
    car_teste = "PA-1506807-7B4C7F0A3D2E1B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"[*] Iniciando análise para CAR: {car_teste[:30]}...")
    
    try:
        response = requests.post(
            'https://laudoesg.com/api/v1/analises/iniciar',
            headers=headers,
            json={
                "numero_car": car_teste,
                "nome_propriedade": "Teste Diagnóstico"
            },
            timeout=120,  # Timeout maior para análise completa
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            print(f"\n   ✅ Análise concluída!")
            print(f"   Score ESG: {data.get('score_esg', 'N/A')}/100")
            print(f"   Status: {data.get('status', 'N/A')}")
            
            # Analisar cada componente
            print(f"\n   📊 DETALHAMENTO POR FONTE:")
            
            # Desmatamento
            dm = data.get('desmatamento', {})
            if dm:
                fonte_dm = dm.get('fonte', 'N/A')
                print(f"   - Desmatamento: {fonte_dm}")
                if 'simulado' in fonte_dm.lower():
                    print("     ⚠️  Simulado")
                elif 'prodes' in fonte_dm.lower():
                    print("     ✅ Real (PRODES/INPE)")
            
            # Áreas protegidas
            ap = data.get('areas_protegidas', {})
            for tipo, resultado in ap.items():
                if isinstance(resultado, dict):
                    fonte = resultado.get('fonte', 'N/A')
                    print(f"   - {tipo}: {fonte}")
            
            # Embargos
            emb = data.get('embargos', {})
            for orgao, resultado in emb.items():
                if isinstance(resultado, dict):
                    fonte = resultado.get('fonte', 'N/A')
                    verificado = resultado.get('verificado', False)
                    print(f"   - Embargo {orgao}: {fonte} (Verificado: {verificado})")
            
            # Conformidade
            conf = data.get('conformidade', {})
            eudr = conf.get('eudr', {})
            if eudr:
                fonte_eudr = eudr.get('fonte', 'N/A')
                print(f"   - EUDR: {fonte_eudr}")
            
            moratoria = conf.get('moratoria_soja', {})
            if moratoria:
                fonte_mor = moratoria.get('fonte', 'N/A')
                print(f"   - Moratória Soja: {fonte_mor}")
                
        else:
            print(f"   ❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def test_apis_externas():
    """Testa APIs externas diretamente"""
    print("\n\n[3] Testando APIs EXTERNAS DIRETAMENTE")
    print("-" * 80)
    
    apis = [
        {
            "nome": "SICAR Nacional - GeoServer",
            "url": "https://geoserver.car.gov.br/geoserver/sicar/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=sicar:sicar_imoveis_pa&CQL_FILTER=cod_imovel='PA-1506807-7B4C7F0A3D2E1B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4'&outputFormat=application/json",
            "desc": "Dados reais de CAR do governo federal"
        },
        {
            "nome": "TerraBrasilis PRODES",
            "url": "https://terrabrasilis.dpi.inpe.br/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=prodes-legal-amz:yearly_deforestation&outputFormat=application/json&count=1",
            "desc": "Desmatamento real do INPE"
        },
        {
            "nome": "SEMAS-PA GeoServer",
            "url": "https://car.semas.pa.gov.br/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=semas:car_validado_semas_pa&CQL_FILTER=numero_car='PA-1506807-7B4C7F0A3D2E1B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4B6A8C9F0E2D4'&outputFormat=application/json",
            "desc": "Dados de CAR do Pará"
        },
        {
            "nome": "CNUC/MMA - Unidades de Conservação",
            "url": "https://sistemas.mma.gov.br/cnuc/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=cnuc:uc_federal&outputFormat=application/json&count=1",
            "desc": "Áreas protegidas (UC)"
        }
    ]
    
    for api in apis:
        print(f"\n[*] {api['nome']}")
        print(f"   Descrição: {api['desc']}")
        
        try:
            # Ignorar SSL para testes
            resp = requests.get(api['url'], timeout=30, verify=False)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                features = data.get('features', [])
                
                print(f"   ✅ API RESPONDEU")
                print(f"   Features encontradas: {len(features)}")
                
                if len(features) > 0:
                    print(f"   ✅ DADOS REAIS DISPONÍVEIS")
                    # Mostrar primeiro feature
                    feat = features[0]
                    props = feat.get('properties', {})
                    if props:
                        keys = list(props.keys())[:5]
                        print(f"   Propriedades: {', '.join(keys)}...")
                else:
                    print(f"   ⚠️  API funciona mas sem dados para este filtro")
                    
            elif resp.status_code == 403:
                print(f"   ❌ Acesso negado (403) - pode precisar de autenticação")
            elif resp.status_code == 404:
                print(f"   ❌ Endpoint não encontrado (404)")
            else:
                print(f"   ❌ Erro: {resp.status_code}")
                
        except requests.exceptions.SSLError as e:
            print(f"   ❌ Erro SSL: {e}")
            print(f"   💡 Dica: O SICAR tem problemas de certificado SSL")
        except Exception as e:
            print(f"   ❌ Erro de conexão: {e}")

def main():
    """Executa todos os testes"""
    print("=" * 80)
    print("DIAGNÓSTICO COMPLETO DAS APIS - EUREKA TERRA")
    print("=" * 80)
    print(f"Iniciado em: {datetime.now()}")
    
    # Fazer login
    token = test_login()
    
    if token:
        print("\n✅ Login bem-sucedido!")
        
        # Testar busca CAR
        test_busca_car(token)
        
        # Testar análise completa
        test_analise_completa(token)
    else:
        print("\n❌ Não foi possível fazer login. Testando APIs externas apenas...")
    
    # Testar APIs externas
    test_apis_externas()
    
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    main()
