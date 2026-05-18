import httpx
car = "PA-1504752-CDA11C2365C740678DDC06AC43C07874"
r = httpx.get("https://geoserverdw.apps.geoapplications.net/geoserver/wfs/", params={
    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
    "typeName": "workspace_sicar:vw_car",
    "CQL_FILTER": f"tx_cod_imovel='{car}'",
    "outputFormat": "application/json", "count": "1",
}, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
props = r.json()["features"][0]["properties"]
for k, v in props.items():
    print(f"  {k}: {str(v)[:60]}")
