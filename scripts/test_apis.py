import httpx
h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# 1. SEMAS-PA
print('=== SEMAS-PA (GeoJSON) ===')
try:
    r = httpx.get('https://car.semas.pa.gov.br/geoserver/wfs', params={
        'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
        'typeName': 'ldi:ldi_areas_embargadas', 'outputFormat': 'application/json',
        'count': 1
    }, headers=h, timeout=15, verify=False)
    print(f'Status: {r.status_code}, Size: {len(r.content)} bytes')
except Exception as e:
    print(f'Erro: {e}')

# 2. CNUC - testar URLs alternativas
print()
print('=== CNUC/MMA (testando URLs) ===')
urls = [
    'https://sistemas.mma.gov.br/cnuc/wfs',
    'https://geoserver.mma.gov.br/geoserver/wfs',
    'https://cnuc.mma.gov.br/geoserver/wfs',
]
for url in urls:
    try:
        r = httpx.get(url, params={'service': 'WFS', 'version': '1.1.0', 'request': 'GetCapabilities'},
                      headers=h, timeout=10, verify=False)
        print(f'{url}: {r.status_code}')
    except Exception as e:
        print(f'{url}: {type(e).__name__}')

# 3. Assentamentos
print()
print('=== INCRA Assentamentos ===')
for tn in ['CMR-PUBLICO:projetoassentamento', 'CMR-PUBLICO:lim_assentamento_rural_a']:
    try:
        r = httpx.get('https://cmr.funai.gov.br/geoserver/wfs', params={
            'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
            'typeName': tn, 'outputFormat': 'application/json', 'count': 1
        }, headers=h, timeout=15, verify=False)
        print(f'  {tn}: {r.status_code}, {len(r.content)} bytes')
    except Exception as e:
        print(f'  {tn}: {type(e).__name__} - {e}')

# 4. FUNAI TI
print()
print('=== FUNAI TI ===')
try:
    r = httpx.get('https://geoserver.funai.gov.br/geoserver/Funai/wfs', params={
        'service': 'WFS', 'version': '1.1.0', 'request': 'GetFeature',
        'typeNames': 'Funai:tis_homologadas', 'outputFormat': 'application/json',
        'maxFeatures': 3
    }, headers=h, timeout=15, verify=False)
    print(f'Status: {r.status_code}, {len(r.content)} bytes')
    data = r.json()
    feats = data.get('features', [])
    print(f'Features: {len(feats)}')
    if feats:
        nome = feats[0].get("properties", {}).get("terrai_nom", "N/A")
        print(f'Primeiro: {nome[:80]}')
    else:
        print('Vazio ou erro: ' + r.text[:200])
except Exception as e:
    print(f'Erro: {e}')
