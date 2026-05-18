import httpx
h = {'User-Agent': 'Mozilla/5.0'}

# FUNAI — ver conteudo real
print("=== FUNAI TI ===")
r = httpx.get('https://geoserver.funai.gov.br/geoserver/Funai/wfs', params={
    'service': 'WFS', 'version': '1.1.0', 'request': 'GetFeature',
    'typeNames': 'Funai:tis_homologadas', 'outputFormat': 'application/json',
    'maxFeatures': 3
}, headers=h, timeout=15, verify=False)
print(f'Status: {r.status_code}, Content-Type: {r.headers.get("content-type", "?")}')
print(f'Body (first 800 chars):')
print(r.text[:800])
print('...')

# CNUC — nova URL
print()
print("=== CNUC/MMA (nova URL) ===")
r2 = httpx.get('https://cnuc.mma.gov.br/geoserver/wfs', params={
    'service': 'WFS', 'version': '1.1.0', 'request': 'GetFeature',
    'typeNames': 'cnuc:unidades_conservacao', 'outputFormat': 'application/json',
    'maxFeatures': 3
}, headers=h, timeout=30, verify=False)
print(f'Status: {r2.status_code}, {len(r2.content)} bytes')
if r2.status_code == 200:
    try:
        d = r2.json()
        print(f'Features: {len(d.get("features", []))}')
        if d.get('features'):
            print(f'Exemplo: {d["features"][0].get("properties", {}).get("nome_uc", "N/A")[:60]}')
    except Exception as e:
        print(f'JSON error: {e}')
        print(r2.text[:300])

# Assentamentos — typename correto
print()
print("=== Assentamentos INCRA (typename correto) ===")
r3 = httpx.get('https://cmr.funai.gov.br/geoserver/wfs', params={
    'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
    'typeName': 'CMR-PUBLICO:lim_assentamento_rural_a',
    'outputFormat': 'application/json', 'count': 3
}, headers=h, timeout=30, verify=False)
print(f'Status: {r3.status_code}, {len(r3.content)} bytes')
if r3.status_code == 200:
    try:
        d = r3.json()
        print(f'Features: {len(d.get("features", []))}')
        if d.get('features'):
            print(f'Exemplo: {d["features"][0].get("properties", {}).get("nom_proje", "N/A")[:60]}')
    except Exception as e:
        print(f'JSON error: {e}')
