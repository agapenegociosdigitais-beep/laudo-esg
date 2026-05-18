import httpx
h = {'User-Agent': 'Mozilla/5.0'}

# FUNAI — GetCapabilities para achar layers validas
print("=== FUNAI GetCapabilities (procurando layers) ===")
r = httpx.get('https://geoserver.funai.gov.br/geoserver/Funai/wfs', params={
    'service': 'WFS', 'version': '1.1.0', 'request': 'GetCapabilities',
}, headers=h, timeout=15, verify=False)
print(f'Status: {r.status_code}, {len(r.content)} bytes')
import re
layers = re.findall(r'<Name>(Funai:[^<]+)</Name>', r.text)
print(f'Layers encontradas ({len(layers)}):')
for l in layers[:15]:
    print(f'  {l}')

# Assentamentos — propriedades disponiveis
print()
print("=== Assentamentos INCRA (propriedades) ===")
r2 = httpx.get('https://cmr.funai.gov.br/geoserver/wfs', params={
    'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
    'typeName': 'CMR-PUBLICO:lim_assentamento_rural_a',
    'outputFormat': 'application/json', 'count': 2
}, headers=h, timeout=30, verify=False)
data = r2.json()
feat = data['features'][0]['properties'] if data.get('features') else {}
print('Propriedades disponiveis:')
for k, v in feat.items():
    print(f'  {k}: {str(v)[:60]}')

# Testar SHAPE-ZIP para Assentamentos
print()
print("=== Assentamentos SHAPE-ZIP ===")
r3 = httpx.get('https://cmr.funai.gov.br/geoserver/wfs', params={
    'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
    'typeName': 'CMR-PUBLICO:lim_assentamento_rural_a',
    'outputFormat': 'SHAPE-ZIP',
}, headers=h, timeout=60, verify=False)
print(f'Status: {r3.status_code}, {len(r3.content)} bytes')
