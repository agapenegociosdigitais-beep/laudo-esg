import httpx
h = {'User-Agent': 'Mozilla/5.0'}
base = 'https://geoserverdw.apps.geoapplications.net/geoserver/wfs/'

# Testar SHAPE-ZIP download em varias layers
layers = [
    'workspace_sicar:vw_sicar_embargos',
    'workspace_sicar:vw_sicar_terras_indigenas',
    'workspace_sicar:vw_sicar_unidades_conservacao',
    'workspace_sicar:vw_sicar_areas_quilombolas',
    'workspace_sicar:vw_sicar_assentamentos',
    'workspace_sicar:vw_car_ativo',
    'workspace_sicar:mv_desmatamento_prodes_2008',
    'workspace_sicar:vw_sicar_autos_de_infracao',
]

for layer in layers:
    try:
        r = httpx.get(base, params={
            'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
            'typeName': layer, 'outputFormat': 'SHAPE-ZIP', 'count': '5',
        }, headers=h, timeout=60, verify=False)
        is_zip = r.content[:2] == b'PK'
        size_kb = len(r.content) / 1024
        print(f'[{r.status_code}] {layer.split(":")[-1][:50]}')
        print(f'  Size: {size_kb:.0f} KB | ZIP: {is_zip} | CT: {r.headers.get("content-type","?")[:50]}')
        if not is_zip and r.status_code == 200:
            print(f'  Body: {r.text[:150]}')
        print()
    except Exception as e:
        print(f'[ERR] {layer.split(":")[-1][:50]}: {e}')
        print()
