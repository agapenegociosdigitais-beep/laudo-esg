#!/usr/bin/env python3
"""
Script de teste de conectividade para APIs externas do Eureka Terra.
Testa cada API externa para identificar falhas de conectividade, SSL, timeout ou DNS.
"""
import asyncio
import sys
import httpx
import ssl
import time
from typing import Dict, Any

# Configurações de timeout
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
        "verify_ssl": False,  # SEMAS-PA usa certificado problemático
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
        "verify_ssl": False,  # SICAR também tem problemas de SSL
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
        "verify_ssl": False,  # INCRA usa certificado problemático
    },
    "IBAMA CTF": {
        "url": "https://servicos.ibama.gov.br/ctf/publico/areasembargadas/consultar",
        "params": {"numeroCar": "PA-1501451-110F7A95501049E282B11240815ECA81"},
        "verify_ssl": True,
    },
}


async def test_api(name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Testa uma API específica e retorna resultado."""
    result = {
        "name": name,
        "url": config["url"],
        "status": "unknown",
        "error": None,
        "response_time": 0,
        "details": {},
    }
    
    start_time = time.time()
    
    try:
        # Cria cliente HTTP com ou sem verificação SSL
        verify_ssl = config.get("verify_ssl", True)
        if not verify_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = True
        
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            verify=ssl_context,
            headers={"User-Agent": "EurekaTerra-Connectivity-Test/1.0"},
        ) as client:
            # Faz requisição GET com parâmetros se existirem
            params = config.get("params")
            if params:
                response = await client.get(config["url"], params=params)
            else:
                response = await client.get(config["url"])
            
            response_time = time.time() - start_time
            result["response_time"] = round(response_time, 2)
            
            # Verifica status code
            if response.status_code == 200:
                result["status"] = "success"
                result["details"]["status_code"] = response.status_code
                result["details"]["content_type"] = response.headers.get("content-type", "unknown")
                
                # Tenta parsear JSON se for aplicação/json
                if "application/json" in response.headers.get("content-type", ""):
                    try:
                        data = response.json()
                        result["details"]["json_keys"] = list(data.keys()) if isinstance(data, dict) else "list"
                        result["details"]["total_features"] = len(data.get("features", []))
                    except Exception as e:
                        result["details"]["json_error"] = str(e)
            else:
                result["status"] = "error"
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                result["details"]["status_code"] = response.status_code
    
    except httpx.TimeoutException as e:
        result["status"] = "timeout"
        result["error"] = f"Timeout após {TIMEOUT}s: {str(e)}"
        result["response_time"] = round(time.time() - start_time, 2)
    
    except httpx.ConnectError as e:
        result["status"] = "connection_error"
        result["error"] = f"Erro de conexão: {str(e)}"
        result["response_time"] = round(time.time() - start_time, 2)
    
    except httpx.HTTPError as e:
        result["status"] = "http_error"
        result["error"] = f"HTTP error: {str(e)}"
        result["response_time"] = round(time.time() - start_time, 2)
    
    except Exception as e:
        result["status"] = "exception"
        result["error"] = f"Exception: {type(e).__name__}: {str(e)}"
        result["response_time"] = round(time.time() - start_time, 2)
    
    return result


async def main():
    """Executa testes de conectividade para todas as APIs."""
    print("=" * 80)
    print("Eureka Terra - Teste de Conectividade com APIs Externas")
    print("=" * 80)
    print(f"Timeout configurado: {TIMEOUT}s")
    print(f"Total de APIs para testar: {len(APIS)}")
    print()
    
    results = []
    
    # Testa cada API
    for name, config in APIS.items():
        print(f"\n[{'='*78}]")
        print(f"Testando: {name}")
        print(f"URL: {config['url']}")
        print(f"SSL Verify: {config.get('verify_ssl', True)}")
        print("-" * 80)
        
        result = await test_api(name, config)
        results.append(result)
        
        # Imprime resultado
        print(f"Status: {result['status'].upper()}")
        print(f"Tempo de resposta: {result['response_time']}s")
        
        if result['error']:
            print(f"Erro: {result['error']}")
        
        if result['details']:
            print("Detalhes:")
            for key, value in result['details'].items():
                print(f"  {key}: {value}")
        
        # Pequena pausa entre requisições para não sobrecarregar
        await asyncio.sleep(0.5)
    
    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)
    
    status_counts = {}
    for result in results:
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        print(f"{status.upper()}: {count}")
    
    print(f"\nTotal: {len(results)} APIs testadas")
    
    # Lista APIs com problemas
    problem_apis = [r for r in results if r['status'] != 'success']
    if problem_apis:
        print("\nAPIs COM PROBLEMAS:")
        for api in problem_apis:
            print(f"  - {api['name']}: {api['status']} - {api['error']}")
    else:
        print("\n✓ Todas as APIs responderam com sucesso!")
    
    # Retorna código de saída baseado nos resultados
    sys.exit(0 if not problem_apis else 1)


if __name__ == "__main__":
    asyncio.run(main())
