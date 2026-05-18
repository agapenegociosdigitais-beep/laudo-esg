#!/usr/bin/env python3
"""
Diagnóstico completo do CAR real para identificar por que retorna dados simulados
"""
import asyncio
import sys
sys.path.insert(0, 'c:\\Users\\benja\\Desktop\\eureka-terra\\backend')

from app.services.semas_service import _normalizar_car_semas, buscar_car_semas
from app.services.sicar_service import buscar_car_sicar

# CAR que você digitou
CAR_ORIGINAL = "PA-1506807-B60D.E267.CD0E.4397.A8D7.5B22.FDB9.91BB"

async def diagnosticar_car():
    print("=" * 80)
    print("DIAGNÓSTICO COMPLETO DO CAR")
    print("=" * 80)
    print(f"\nCAR Original: {CAR_ORIGINAL}")
    
    # Normalizar para SEMAS
    car_normalizado = _normalizar_car_semas(CAR_ORIGINAL)
    print(f"CAR Normalizado (SEMAS): {car_normalizado}")
    
    # Testar SEMAS-PA
    print("\n" + "=" * 80)
    print("TESTE 1: SEMAS-PA GeoServer")
    print("=" * 80)
    try:
        resultado_semas = await buscar_car_semas(CAR_ORIGINAL)
        print(f"✓ Chamada concluída")
        print(f"Sucesso: {resultado_semas.get('sucesso')}")
        print(f"Mensagem: {resultado_semas.get('erro', 'Sem erro')}")
        if resultado_semas.get('sucesso'):
            print(f"Status: {resultado_semas.get('status')}")
            print(f"Área: {resultado_semas.get('area_ha')} ha")
            print(f"Município: {resultado_semas.get('municipio')}")
            print(f"Fonte: {resultado_semas.get('fonte')}")
        else:
            print("⚠️  SEMAS-PA não encontrou o CAR")
    except Exception as e:
        print(f"❌ Erro ao chamar SEMAS-PA: {e}")
    
    # Testar SICAR Nacional
    print("\n" + "=" * 80)
    print("TESTE 2: SICAR Nacional GeoServer")
    print("=" * 80)
    try:
        resultado_sicar = await buscar_car_sicar(CAR_ORIGINAL)
        print(f"✓ Chamada concluída")
        print(f"Sucesso: {resultado_sicar.get('sucesso')}")
        print(f"Mensagem: {resultado_sicar.get('erro', 'Sem erro')}")
        if resultado_sicar.get('sucesso'):
            print(f"Status: {resultado_sicar.get('status')}")
            print(f"Área: {resultado_sicar.get('area_ha')} ha")
            print(f"Município: {resultado_sicar.get('municipio')}")
            print(f"Fonte: {resultado_sicar.get('fonte')}")
        else:
            print("⚠️  SICAR não encontrou o CAR")
    except Exception as e:
        print(f"❌ Erro ao chamar SICAR: {e}")
    
    # Análise final
    print("\n" + "=" * 80)
    print("ANÁLISE FINAL")
    print("=" * 80)
    print("\n🔍 Possíveis causas para dados simulados:")
    print("   1. CAR não existe nas bases oficiais (inválido)")
    print("   2. CAR está com formato incorreto (pontos no identificador)")
    print("   3. Serviços externos estão fora do ar")
    print("   4. Timeout nas requisições")
    print("\n💡 Soluções:")
    print("   • Verificar se o CAR é válido no site do SICAR")
    print("   • Testar com CAR sem pontos no identificador")
    print("   • Verificar logs do backend em tempo real")
    print("   • Testar conectividade com os serviços externos")

if __name__ == "__main__":
    asyncio.run(diagnosticar_car())