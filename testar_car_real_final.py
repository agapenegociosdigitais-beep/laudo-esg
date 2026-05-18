#!/usr/bin/env python3
"""
Teste final: Verificar se o CAR real agora retorna dados reais após correção de SSL
"""
import asyncio
import sys
sys.path.insert(0, 'c:\\Users\\benja\\Desktop\\eureka-terra\\backend')

from app.services.car_service import CARService
from app.services.semas_service import buscar_car_semas
from app.services.sicar_service import buscar_car_sicar

# CAR real que você digitou
CAR_REAL = "PA-1506807-B60D.E267.CD0E.4397.A8D7.5B22.FDB9.91BB"

async def testar_car_real():
    print("=" * 80)
    print("TESTE FINAL - CAR REAL APÓS CORREÇÃO SSL")
    print("=" * 80)
    print(f"\nCAR sendo testado: {CAR_REAL}")
    print("-" * 80)
    
    # Testar SICAR Nacional (prioridade)
    print("\n[1/3] Testando SICAR Nacional...")
    try:
        resultado_sicar = await buscar_car_sicar(CAR_REAL)
        
        if resultado_sicar.get('sucesso'):
            print("✅ SICAR encontrou o CAR!")
            print(f"   Status: {resultado_sicar.get('status')}")
            print(f"   Área: {resultado_sicar.get('area_ha')} ha")
            print(f"   Município: {resultado_sicar.get('municipio')}")
            print(f"   Fonte: {resultado_sicar.get('fonte')}")
            print(f"   Geometria: {'Sim' if resultado_sicar.get('geometria') else 'Não'}")
        else:
            print(f"❌ SICAR não encontrou: {resultado_sicar.get('erro')}")
    except Exception as e:
        print(f"❌ Erro no SICAR: {e}")
    
    # Testar SEMAS-PA
    print("\n[2/3] Testando SEMAS-PA...")
    try:
        resultado_semas = await buscar_car_semas(CAR_REAL)
        
        if resultado_semas.get('sucesso'):
            print("✅ SEMAS-PA encontrou o CAR!")
            print(f"   Status: {resultado_semas.get('status')}")
            print(f"   Área: {resultado_semas.get('area_ha')} ha")
            print(f"   Município: {resultado_semas.get('municipio')}")
            print(f"   Fonte: {resultado_semas.get('fonte')}")
        else:
            print(f"❌ SEMAS-PA não encontrou: {resultado_semas.get('erro')}")
    except Exception as e:
        print(f"❌ Erro no SEMAS-PA: {e}")
    
    # Testar serviço completo (car_service)
    print("\n[3/3] Testando serviço completo (car_service)...")
    try:
        service = CARService()
        resultado_final = await service.buscar_por_car(CAR_REAL)
        
        print(f"✅ Serviço concluído!")
        print(f"   Encontrado: {resultado_final.encontrado}")
        print(f"   Fonte: {resultado_final.fonte}")
        print(f"   Status: {resultado_final.status_car}")
        print(f"   Área: {resultado_final.area_ha} ha")
        print(f"   Município: {resultado_final.municipio}")
        
        if "simulado" in resultado_final.fonte.lower() or "demo" in resultado_final.fonte.lower():
            print("\n⚠️  ATENÇÃO: Ainda retornando dados simulados!")
            print("   Isso significa que ambos os serviços falharam.")
        else:
            print("\n🎉 SUCESSO! Retornando dados REAIS!")
            
    except Exception as e:
        print(f"❌ Erro no serviço completo: {e}")
    
    print("\n" + "=" * 80)
    print("TESTE CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(testar_car_real())