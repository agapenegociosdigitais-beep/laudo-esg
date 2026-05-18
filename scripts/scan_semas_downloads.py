import httpx, re
h = {'User-Agent': 'Mozilla/5.0'}
base = 'https://portal-servicos-sistemas.semas.pa.gov.br'

urls = [
    '/outros-conteudos-sicar+bases-de-referencia+684cad6482f5e7699fac8e8a',
    '/outros-conteudos-sicar/bases-de-referencia/684cad6482f5e7699fac8e8a',
    '/i/684cad6482f5e7699fac8e8a',
    '/materiais-apoio',
    '/consulta-geral',
    '/regularizacao-ambiental',
    '/consultas',
    '/outros-servicos',
    '/one-form-guest',
]

for url in urls:
    try:
        r = httpx.get(base + url, headers=h, timeout=15, verify=False, follow_redirects=True)
        ct = r.headers.get('content-type','?')[:40]
        text = r.text

        # Links de download
        downloads = re.findall(r"""href=["']([^"']*\.(?:zip|shp|geojson|json|csv|pdf|rar|7z))["']""", text, re.I)

        print(f'[{r.status_code}] {url} ({len(r.content)}B) ct={ct}')
        if downloads:
            for d in downloads[:5]:
                full = base + d if d.startswith('/') else d
                print(f'  >> DOWNLOAD: {full[:120]}')
        # Buscar palavras-chave
        if 'shape' in text.lower() or 'download' in text.lower() or 'referencia' in text.lower():
            print(f'  CONTEM: shape/download/referencia')
    except Exception as e:
        print(f'[ERR] {url}: {type(e).__name__}')

# Verificar tambem o dominio antigo de monitoramento
print()
print('=== monitoramento.semas.pa.gov.br ===')
for path in ['/ldi/', '/', '/downloads/', '/arquivos/', '/bases/']:
    try:
        r = httpx.get(f'https://monitoramento.semas.pa.gov.br{path}', headers=h, timeout=10, verify=False)
        print(f'[{r.status_code}] {path} ({len(r.content)}B)')
        downloads = re.findall(r"""href=["']([^"']*\.(?:zip|shp|geojson|json|csv))["']""", r.text, re.I)
        if downloads:
            for d in downloads[:3]:
                print(f'  >> DOWNLOAD: {d}')
    except Exception as e:
        print(f'[ERR] {path}: {type(e).__name__}')
