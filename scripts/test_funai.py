import httpx
h = {'User-Agent': 'Mozilla/5.0'}

# Testar FUNAI com layer correta
print("=== FUNAI tis_poligonais (propriedades) ===")
r = httpx.get('https://geoserver.funai.gov.br/geoserver/Funai/wfs', params={
    'service': 'WFS', 'version': '1.1.0', 'request': 'GetFeature',
    'typeNames': 'Funai:tis_poligonais',
    'outputFormat': 'application/json', 'maxFeatures': 2
}, headers=h, timeout=30, verify=False)
print(f'Status: {r.status_code}, {len(r.content)} bytes')
data = r.json()
feat = data['features'][0]['properties'] if data.get('features') else {}
print('Propriedades disponiveis:')
for k, v in feat.items():
    print(f'  {k}: {str(v)[:80]}')

print()

# Testar SHAPE-ZIP para FUNAI
print("=== FUNAI SHAPE-ZIP ===")
r2 = httpx.get('https://geoserver.funai.gov.br/geoserver/Funai/wfs', params={
    'service': 'WFS', 'version': '1.1.0', 'request': 'GetFeature',
    'typeNames': 'Funai:tis_poligonais',
    'outputFormat': 'SHAPE-ZIP',
}, headers=h, timeout=120, verify=False)
print(f'Status: {r2.status_code}, {len(r2.content)} bytes')
if r2.status_code == 200 and len(r2.content) > 1000:
    print('SHAPE-ZIP OK!')
