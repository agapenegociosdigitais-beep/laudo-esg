import httpx
h = {'User-Agent': 'Mozilla/5.0'}

urls = [
    ('GeoServer antigo', 'https://car.semas.pa.gov.br/geoserver/ows?service=WFS&version=2.0.0&request=GetCapabilities'),
    ('GeoServer monitoramento', 'https://monitoramento.semas.pa.gov.br/geoserver/ows?service=WFS&version=2.0.0&request=GetCapabilities'),
    ('Portal novo API base', 'https://portal-servicos-sistemas.semas.pa.gov.br/api/1/'),
    ('LDI antigo', 'https://monitoramento.semas.pa.gov.br/ldi/'),
    ('LDI pesquisa', 'https://monitoramento.semas.pa.gov.br/ldi/pesquisa/pesquisarComCar?codigoImovel=PA-1506807-B60DE267CD0E4397A8D75B22FDB991BB'),
]

for label, url in urls:
    try:
        r = httpx.get(url, headers=h, timeout=15, verify=False, follow_redirects=True)
        ct = r.headers.get('content-type', '?')[:60]
        body_preview = r.text[:150] if len(r.text) > 0 else '(vazio)'
        print(f'[{r.status_code}] {label}')
        print(f'  Type: {ct}')
        print(f'  Body: {body_preview}')
        print()
    except Exception as e:
        print(f'[ERR] {label}: {type(e).__name__}: {e}')
        print()
