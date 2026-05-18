import httpx, json
h = {'User-Agent': 'Mozilla/5.0'}
base = 'https://geoserverdw.apps.geoapplications.net/geoserver/wfs/'

layers = [
    'workspace_sicar:vw_sicar_embargos',
    'workspace_sicar:vw_sicar_terras_indigenas',
    'workspace_sicar:vw_sicar_unidades_conservacao',
    'workspace_sicar:vw_sicar_areas_quilombolas',
    'workspace_sicar:vw_sicar_assentamentos',
    'workspace_sicar:vw_car_ativo',
    'workspace_sicar:mv_desmatamento_prodes_2008',
    'workspace_sicar:vw_sicar_autos_de_infracao',
    'workspace_sicar:vw_florestas_publicas_2024',
    'workspace_fiscalizacao_inteligente:vw_alertas_deter',
    'workspace_sicar:vw_sicar_imoveis',
]

for layer in layers:
    try:
        r = httpx.get(base, params={
            'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
            'typeName': layer, 'outputFormat': 'application/json', 'count': '1',
        }, headers=h, timeout=30, verify=False)
        data = r.json()
        feats = data.get('features', [])
        short = layer.split(':')[-1]
        if feats:
            props = feats[0].get('properties', {})
            # Mostrar nome da coluna e exemplo do valor
            print(f'=== {short} ({len(props)} columns) ===')
            for k, v in props.items():
                print(f'  {k}: {str(v)[:60]}')
        else:
            print(f'=== {short}: VAZIO ===')
        print()
    except Exception as e:
        print(f'=== {layer.split(":")[-1]}: ERRO - {e}')
        print()
