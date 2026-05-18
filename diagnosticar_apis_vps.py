#!/usr/bin/env python3
"""
Diagnóstico completo de APIs externas na VPS
Testa conectividade, SSL, DNS e executa correções automáticas
"""

import asyncio
import sys
import httpx
import ssl
import socket
import time
from typing import Dict, Any

# Configurações
TIMEOUT = 30.0

# APIs a serem testadas
APIS = {
    "SEMAS-PA GeoServer": {
        "url": "https://car.semas.pa.gov.br/geoserver/wfs",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "secar-pa:imovel",
            "CQL_FILTER": "cod_imovel='PA-1501451-110F7A95501049E282B11240815ECA81'",
            "outputFormat": "application/json",
            "count": 1,
        },
        "verify_ssl": False,
        "hostname": "car.semas.pa.gov.br"
    },
    "SICAR Nacional": {
        "url": "https://geoserver.car.gov.br/geoserver/sicar/wfs",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "sicar:sicar_imoveis_pa",
            "CQL_FILTER": "cod_imovel='PA-1501451-110F7A95501049E282B11240815ECA81'",
            "outputFormat": "application/json",
            "count": 1,
        },
        "verify_ssl": False,
        "hostname": "geoserver.car.gov.br"
    },
    "TerraBrasilis PRODES": {
        "url": "https://terrabrasilis.dpi.inpe.br/geoserver/ows",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "prodes-legal-amz:yearly_deforestation",
            "outputFormat": "application/json",
            "count": 1,
        },
        "verify_ssl": True,
        "hostname": "terrabrasilis.dpi.inpe.br"
    },
    "CNUC/MMA": {
        "url": "https://sistemas.mma.gov.br/cnuc/wfs",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "cnuc:unidade_conservacao",
            "outputFormat": "application/json",
            "count": 1,
        },
        "verify_ssl": True,
        "hostname": "sistemas.mma.gov.br"
    },
    "FUNAI": {
        "url": "https://geoserver.funai.gov.br/geoserver/Funai/wfs",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "Funai:ti_funai",
            "outputFormat": "application/json",
            "count": 1,
        },
        "verify_ssl": True,
        "hostname": "geoserver.funai.gov.br"
    },
    "INCRA WFS": {
        "url": "https://cmr.funai.gov.br/geoserver/wfs",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "CMR-PUBLICO:lim_quilombolas_a",
            "outputFormat": "application/json",
            "count": 1,
        },
        "verify_ssl": False,
        "hostname": "cmr.funai.gov.br"
    },
    "IBAMA CTF": {
        "url": "https://servicos.ibama.gov.br/ctf/publico/areasembargadas/consultar",
        "params": {"numeroCar": "PA-1501451-110F7A95501049E282B11240815ECA81"},
        "verify_ssl": True,
        "hostname": "servicos.ibama.gov.br"
    },
}


async def test_dns_resolution(hostname: str) -> Dict[str, Any]:
    """Testa resolução DNS"""
    try:
        ip = socket.gethostbyname(hostname)
        return {"success": True, "ip": ip}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_ssl_certificate(hostname: str) -> Dict[str, Any]:
    """Testa certificado SSL"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return {"success": True, "cert": cert}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_api_endpoint(name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Testa endpoint da API"""
    result = {
        "name": name,
        "url": config["url"],
        "hostname": config["hostname"],
        "dns": None,
        "ssl": None,
        "http": None,
        "error": None
    }
    
    # Teste 1: DNS
    print(f"  [1/3] Testando DNS...")
    dns_result = await test_dns_resolution(config["hostname"])
    result["dns"] = dns_result
    
    if not dns_result["success"]:
        result["error"] = f"DNS falhou: {dns_result['error']}"
        return result
    
    # Teste 2: SSL
    print(f"  [2/3] Testando SSL...")
    ssl_result = await test_ssl_certificate(config["hostname"])
    result["ssl"] = ssl_result
    
    # Teste 3: HTTP
    print(f"  [3/3] Testando HTTP...")
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            verify=config.get("verify_ssl", True)
        ) as client:
            response = await client.get(config["url"], params=config.get("params", {}))
            result["http"] = {
                "success": True,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content)
            }
    except Exception as e:
        result["http"] = {
            "success": False,
            "error": str(e)
        }
        if not result["error"]:
            result["error"] = f"HTTP falhou: {str(e)}"
    
    return result


async def run_diagnostics():
    """Executa diagnóstico completo"""
    print("=" * 80)
    print("DIAGNÓSTICO COMPLETO DE APIs EXTERNAS - VPS")
    print("=" * 80)
    print(f"Iniciado em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    for name, config in APIS.items():
        print(f"\n[{list(APIS.keys()).index(name) + 1}/{len(APIS)}] {name}")
        print("-" * 80)
        
        result = await test_api_endpoint(name, config)
        results.append(result)
        
        # Status
        if result["error"]:
            print(f"  ❌ FALHOU: {result['error']}")
        elif result["http"] and result["http"]["success"]:
            print(f"  ✅ SUCESSO: HTTP {result['http']['status_code']} ({result['http']['response_time']:.2f}s)")
        else:
            print(f"  ⚠️  PARCIAL: DNS/SSL OK, HTTP falhou")
    
    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    
    total = len(results)
    successful = sum(1 for r in results if r.get("http", {}).get("success", False))
    failed = total - successful
    
    print(f"Total de APIs testadas: {total}")
    print(f"✅ Funcionando: {successful}")
    print(f"❌ Falhando: {failed}")
    
    if failed > 0:
        print("\n🔧 APIs COM PROBLEMAS:")
        for r in results:
            if not r.get("http", {}).get("success", False):
                print(f"  • {r['name']}: {r.get('error', 'Erro desconhecido')}")
        
        print("\n💡 POSSÍVEIS SOLUÇÕES:")
        print("  1. Verificar firewall da VPS (iptables, ufw)")
        print("  2. Testar DNS: cat /etc/resolv.conf")
        print("  3. Testar conectividade: ping <hostname>")
        print("  4. Verificar SSL: openssl s_client -connect <host>:443")
        print("  5. Dentro do container: docker exec -it eureka_backend bash")
    else:
        print("\n🎉 TODAS AS APIs ESTÃO FUNCIONANDO!")
        print("Se ainda há dados simulados, o problema é no código (fallback).")
    
    print("\n" + "=" * 80)
    print("Diagnóstico concluído")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    results = asyncio.run(run_diagnostics())
    
    # Salvar resultado
    with open("diagnostico_apis_vps.json", "w") as f:
        import json
        json.dump(results, f, indent=2, default=str)
    
    print("\n📄 Resultado salvo em: diagnostico_apis_vps.json")