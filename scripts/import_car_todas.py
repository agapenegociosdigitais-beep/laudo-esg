"""Importa todas as camadas de CAR (ativo, pendente, suspenso, cancelado) para a tabela unificada."""
import httpx, tempfile, zipfile, os, shutil
from io import BytesIO
from pathlib import Path
import geopandas as gpd
import sqlalchemy as sa

engine = sa.create_engine("postgresql://eureka:eurekapass@localhost:5432/eureka_db")
h = {"User-Agent": "Mozilla/5.0"}

COLUNAS = {
    "tx_cod_imo": "cod_imovel", "tx_status_": "status",
    "tx_nome_im": "nome_imovel", "tx_nome_pr": "nome_proprietario",
    "tx_cpf_cnp": "cpf_cnpj", "tx_nome_mu": "municipio",
    "num_area_i": "area_ha", "tx_des_con": "condicao",
    "tx_tipo_im": "tipo_imovel",
}

LAYERS = [
    "workspace_sicar:vw_car_ativo",
    "workspace_sicar:vw_car_pendente",
    "workspace_sicar:vw_car_suspenso",
    "workspace_sicar:vw_car_cancelado",
    "workspace_sicar:vw_car",
]

# Drop e recria tabela unificada
with engine.begin() as conn:
    conn.execute(sa.text("DROP TABLE IF EXISTS cache_car_ativo CASCADE"))
    cols_ddl = ", ".join(f"{v} TEXT" for v in COLUNAS.values())
    conn.execute(sa.text(f"CREATE TABLE cache_car_ativo ({cols_ddl})"))
    conn.execute(sa.text("SELECT AddGeometryColumn('public', 'cache_car_ativo', 'geom', 4326, 'MULTIPOLYGON', 2)"))
    conn.execute(sa.text("CREATE INDEX idx_cache_car_ativo_geom ON cache_car_ativo USING GIST (geom)"))
    conn.execute(sa.text("ALTER TABLE cache_car_ativo ADD CONSTRAINT uq_cache_car_ativo_cod UNIQUE (cod_imovel)"))

for layer in LAYERS:
    nome = layer.split(":")[-1]
    print(f"Baixando {nome}...")
    r = httpx.get(
        "https://geoserverdw.apps.geoapplications.net/geoserver/wfs/",
        params={"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeName": layer, "outputFormat": "SHAPE-ZIP"},
        headers=h, timeout=300, verify=False,
    )
    print(f"  Download: {len(r.content)/1024:.0f} KB")

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(BytesIO(r.content)) as z:
        z.extractall(tmp)
    shp = [f for f in os.listdir(tmp) if f.endswith(".shp")][0]
    gdf = gpd.read_file(Path(tmp) / shp)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)

    col_validas = {k: v for k, v in COLUNAS.items() if k in gdf.columns}
    gdf = gdf.rename(columns=col_validas)
    total = len(gdf)
    print(f"  Registros: {total}")

    inseridos = 0
    for _, row in gdf.iterrows():
        wkt = row.geometry.wkt
        vals = {c: str(row.get(c))[:5000] for c in col_validas.values()
                if row.get(c) is not None and str(row.get(c)) not in ("nan", "None", "")}
        cols = list(vals.keys())
        try:
            with engine.begin() as conn:
                if cols:
                    ph = ", ".join(f":{c}" for c in cols)
                    sql = f"INSERT INTO cache_car_ativo ({', '.join(cols)}, geom) VALUES ({ph}, ST_Multi(ST_Force2D(ST_GeomFromText(:__w, 4326)))) ON CONFLICT (cod_imovel) DO NOTHING"
                    conn.execute(sa.text(sql), {**vals, "__w": wkt})
                else:
                    conn.execute(sa.text("INSERT INTO cache_car_ativo (geom) VALUES (ST_Multi(ST_Force2D(ST_GeomFromText(:__w, 4326)))) ON CONFLICT DO NOTHING"), {"__w": wkt})
            inseridos += 1
        except Exception:
            pass
    print(f"  Inseridos: {inseridos}")
    shutil.rmtree(tmp)

n = engine.connect().execute(sa.text("SELECT COUNT(*) FROM cache_car_ativo")).scalar()
print(f"\nTotal CARs no cache: {n}")
