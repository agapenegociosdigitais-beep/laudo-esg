import httpx

TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..romXiQoWiERS3DBoD28XvQ.soHjUSLBT5BfRFk_Ra-g4cT9Dx8rgoTSk-w4H1YIos14d-RuBbTPSrzhpDz1GNzwvknxzUdJo-O2SYG3WyQbiGw5jRZmClxXWUe9GLlvQ1-vSHPM19sC2mLCOLMly6a5VCaaoMpfab7wIMIwH-cwnJDsol_uoBXyrk_wts2gsUo20i9iz_HjSz6JyjeM1Iq-vqGDDwakD-vyoRg4uRiFlsDOY5hpSsd5zyJdOW48QGff0SrrhUHLlYz-Q4J4AMfbl1969D5SaN5bdCvhGxFlsNKcyvCp0-EEj1BUtHcdtInTELa_VxfK_qmmx-ZaQI9ZYtj9dCsW1Jb_umUcocHbPz4fEUnUBY3id3mY5S600Y9TscbDJUllDHxZMOzivr_WO7z3OUa9bo9FVvGUQDhws2T-uSI74RLKiLdZFXA4gvMHEjHyAaqnEtzA6Fc1ON6MBMeOWnwS0jKR6Z5oGg8ySF1U9fTdNcd2yzoV3VzPZQlamIbYHbKte_32_DYtb4fteGu6aJGaSArnkSUYI1iD85-wACrF0Gqnu68-fNDbUqZvAoCG4ETKavn_lJ-mKSHx8-GuVbTuRrNWC3EspuGkuRrSxidY28HSMbcdTEdQvtmqxodWzCujZsaT7gihYC-YM7DqRzWmko3fn7Rm2twfY9of87Ybu82eeKGWNYfqbb8.9rk6nV6HEQepLnRekrI6gA"

BASE = "https://portal-servicos-sistemas.semas.pa.gov.br/api/1/"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
}

client = httpx.Client(headers=HEADERS, timeout=30, verify=False, follow_redirects=True)

# 1. Buscar o conteudo da pagina "bases de referencia"
content_id = "684cad6482f5e7699fac8e8a"
print(f"=== Conteudo: {content_id} ===")
r = client.get(f"{BASE}servicedesk-embedded/_classId/5ca3bca7d18bdb280c9c6c2c/{content_id}")
print(f"Status: {r.status_code}, {len(r.content)} bytes")
if r.status_code == 200:
    import json
    try:
        data = r.json()
        print(f"Keys: {list(data.keys())[:15]}")
        # Buscar titulo e conteudo
        for key in ['name', 'title', 'description', 'content', 'html', 'body', 'text']:
            if key in data:
                val = str(data[key])[:300]
                print(f"  {key}: {val}")
        # Buscar anexos/arquivos
        for key in data:
            if 'file' in key.lower() or 'attach' in key.lower() or 'url' in key.lower() or 'link' in key.lower():
                print(f"  {key}: {str(data[key])[:200]}")
        # Print all keys at top level
        print(f"\nTodas as chaves: {list(data.keys())}")
    except:
        print(f"Raw: {r.text[:1000]}")

# 2. Buscar o catalogo "outros-conteudos-sicar"
print()
print("=== Buscando conteudos SICAR ===")
r = client.get(f"{BASE}servicedesk-embedded/_classId/5ca3bca7d18bdb280c9c6c2c", params={
    "name": "bases",
    "limit": 10,
})
print(f"Status: {r.status_code}, {len(r.content)} bytes")
if r.status_code == 200:
    try:
        data = r.json()
        print(f"Type: {type(data).__name__}, Len: {len(data) if isinstance(data, list) else 'N/A'}")
        if isinstance(data, list):
            for item in data[:5]:
                print(f"  - {item.get('name', item.get('title', '?'))[:80]} (id={item.get('_id','?')})")
    except:
        print(f"Raw: {r.text[:500]}")

# 3. Tentar buscar shapefiles no GeoServer com token
print()
print("=== GeoServer com token ===")
r = client.get("https://car.semas.pa.gov.br/geoserver/ows", params={
    "service": "WFS", "version": "2.0.0", "request": "GetCapabilities"
})
print(f"GeoServer antigo: {r.status_code}")

# 4. Buscar a lista de catalogs disponiveis
print()
print("=== Catalogs ===")
r = client.get(f"{BASE}servicedesk-embedded/_classId/5ca3bca7d18bdb280c9c6c2c/search", params={
    "limit": 20,
})
print(f"Status: {r.status_code}, {len(r.content)} bytes")
if r.status_code == 200:
    try:
        data = r.json()
        if isinstance(data, list):
            for item in data[:10]:
                print(f"  - {item.get('name', '?')[:70]} (id={item.get('_id','?')})")
    except:
        print(f"Raw: {r.text[:500]}")
