import httpx
h = {'User-Agent': 'Mozilla/5.0'}
car = 'PA-1504752-CDA11C2365C740678DDC06AC43C07874'
layers = ['vw_car_ativo', 'vw_car_pendente', 'vw_car_suspenso', 'vw_car_cancelado', 'vw_car']
for l in layers:
    r = httpx.get('https://geoserverdw.apps.geoapplications.net/geoserver/wfs/', params={
        'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
        'typeName': f'workspace_sicar:{l}',
        'CQL_FILTER': f"tx_cod_imovel='{car}'",
        'outputFormat': 'application/json', 'count': '1',
    }, headers=h, timeout=15, verify=False)
    feats = r.json().get('features', [])
    if feats:
        p = feats[0]['properties']
        print(f'{l}: ENCONTRADO - status={p.get("tx_status_imovel","?")}, nome={p.get("tx_nome_imovel","?")}')
    else:
        print(f'{l}: nao encontrado')
