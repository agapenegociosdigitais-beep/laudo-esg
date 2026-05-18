import httpx
h = {'User-Agent': 'Mozilla/5.0'}
base = 'https://geoserverdw.apps.geoapplications.net/geoserver/wfs/'

for v in ['2.0.0', '1.1.0', '1.0.0']:
    p = {
        'service': 'WFS', 'version': v, 'request': 'GetFeature',
        'typeName': 'workspace_sicar:mv_incremento_desmatamento_prodes_cerrado',
        'outputFormat': 'SHAPE-ZIP', 'count': '3',
    }
    r = httpx.get(base, params=p, headers=h, timeout=15, verify=False)
    print(f'v{v}: {r.status_code}, {len(r.content)}B, ZIP={r.content[:2]==b"PK"}')
    if r.status_code != 200:
        print(f'  Body: {r.text[:200]}')
