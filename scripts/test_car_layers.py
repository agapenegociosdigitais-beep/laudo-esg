import httpx
h = {'User-Agent': 'Mozilla/5.0'}
base = 'https://geoserverdw.apps.geoapplications.net/geoserver/wfs/'

layers = [
    'workspace_sicar:vw_car_ativo',
    'workspace_sicar:vw_car_pendente',
    'workspace_sicar:vw_car_suspenso',
    'workspace_sicar:vw_car_cancelado',
    'workspace_sicar:vw_car',
    'workspace_sicar:vw_sicar_imoveis',
]

for layer in layers:
    try:
        r = httpx.get(base, params={
            'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
            'typeName': layer, 'outputFormat': 'application/json', 'count': '1',
        }, headers=h, timeout=15, verify=False)
        data = r.json()
        n = len(data.get('features', []))
        print(f'{layer.split(":")[-1][:25]:30s} {r.status_code}  {n} features')
        if n > 0:
            props = data['features'][0]['properties']
            print(f'  colunas: {list(props.keys())[:8]}...')
    except Exception as e:
        print(f'{layer.split(":")[-1][:25]:30s} ERR: {e}')
