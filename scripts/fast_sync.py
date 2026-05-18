"""Import rapido usando COPY do PostgreSQL — 100x mais rapido que INSERT."""

import os
import shutil
import sys
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import geopandas as gpd
import httpx
from sqlalchemy import text
import psycopg2

DB = "host=localhost port=5432 user=eureka password=eurekapass dbname=eureka_db"
GEO = "https://geoserverdw.apps.geoapplications.net/geoserver/wfs/"

HEADERS = {"User-Agent": "Mozilla/5.0"}


def sync_fast(tabela: str, layer: str, colunas: dict):
    """Baixa shapefile e importa via COPY (instantaneo)."""
    print(f"Baixando {layer}...")
    resp = httpx.get(GEO, params={
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeName": layer, "outputFormat": "SHAPE-ZIP",
    }, headers=HEADERS, timeout=600, verify=False)
    resp.raise_for_status()
    print(f"  Download: {len(resp.content)/1024:.0f} KB")

    tmp = tempfile.mkdtemp(prefix="sync_")
    try:
        with zipfile.ZipFile(BytesIO(resp.content)) as zf:
            zf.extractall(tmp)
        shp_files = [f for f in os.listdir(tmp) if f.lower().endswith(".shp")]
        if not shp_files:
            raise ValueError(f"Nenhum .shp em {tabela}")
        
        gdf = gpd.read_file(Path(tmp) / shp_files[0])
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(4326)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)

        # Mapeia nomes de coluna (tratando shapefile DBF truncado)
        col_validas = {k: v for k, v in colunas.items() if k in gdf.columns}
        gdf_clean = gdf.rename(columns=col_validas)[list(col_validas.values())]
        
        # Adiciona WKT da geometria
        gdf_clean["_wkt"] = gdf["geometry"].apply(lambda g: g.wkt if g else None)

        # Drop e recria tabela
        conn = psycopg2.connect(DB)
        cur = conn.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {tabela} CASCADE")
        cols_sql = ", ".join(f"{c} TEXT" for c in col_validas.values())
        cur.execute(f"CREATE TABLE {tabela} ({cols_sql})")
        cur.execute(f"SELECT AddGeometryColumn('public', '{tabela}', 'geom', 4326, 'MULTIPOLYGON', 2)")
        conn.commit()

        # COPY em lote
        cols_dest = list(col_validas.values())
        total = len(gdf_clean)
        batch_size = 50000

        for i in range(0, total, batch_size):
            chunk = gdf_clean.iloc[i:i+batch_size]
            with conn.cursor() as c:
                import io
                buf = io.StringIO()
                for _, row in chunk.iterrows():
                    vals = []
                    for col in cols_dest:
                        v = row.get(col)
                        vals.append(str(v).replace("\t", " ").replace("\n", " ") if v is not None and str(v) not in ("nan", "None") else "\\N")
                    wkt = row.get("_wkt", "")
                    vals.append(wkt.replace("\t", " ").replace("\n", " ") if wkt else "\\N")
                    buf.write("\t".join(vals) + "\n")
                buf.seek(0)
                c.copy_from(buf, tabela, columns=cols_dest + ["geom"], null="\\N")
            conn.commit()
            print(f"  {min(i+batch_size, total)}/{total}")

        # Indice espacial
        cur.execute(f"CREATE INDEX idx_{tabela}_geom ON {tabela} USING GIST (geom)")
        conn.commit()
        conn.close()
        return total
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    layers = [
        ("cache_prodes", "workspace_sicar:mv_desmatamento_prodes_2008", {
            "year": "year", "area_km": "area_km", "state": "state",
            "main_class": "main_class", "class_name": "class_name",
            "image_date": "image_date", "path_row": "path_row",
        }),
        ("cache_embargos", "workspace_sicar:vw_sicar_embargos", {
            "tx_num_tad": "num_tad", "tx_seq_tad": "seq_tad",
            "tx_orgao_r": "orgao", "dat_embarg": "data_embargo",
            "area_embar": "area_ha", "tx_nome_in": "nome_infrator",
            "tx_cpf_cnp": "cpf_cnpj", "tx_descric": "descricao",
            "sit_desemb": "situacao",
        }),
        ("cache_alertas_deter", "workspace_fiscalizacao_inteligente:vw_alertas_deter", {
            "data_alerta": "data_alerta", "ano_alerta": "ano",
            "tx_sigla_": "uf", "area_calc_": "area_ha",
            "tx_classe": "classe_alerta",
        }),
        ("cache_florestas_publicas", "workspace_sicar:vw_florestas_publicas_2024", {
            "tx_nome": "nome", "tx_classe": "classe",
            "tx_catego": "categoria", "tx_orgao_": "orgao",
            "area_flor": "area_ha",
        }),
        ("cache_autos_infracao", "workspace_sicar:vw_sicar_autos_de_infracao", {
            "tx_num_au": "num_auto", "dat_lavra": "data_lavratura",
            "tx_tipo_i": "tipo_infracao", "tx_nome_i": "nome_infrator",
            "tx_cpf_cn": "cpf_cnpj", "tx_orgao_": "orgao",
        }),
        ("cache_car_ativo", "workspace_sicar:vw_car_ativo", {
            "tx_cod_imo": "cod_imovel", "tx_status_": "status",
            "tx_nome_im": "nome_imovel", "tx_nome_pr": "nome_proprietario",
            "tx_cpf_cnp": "cpf_cnpj", "tx_nome_mu": "municipio",
            "num_area_i": "area_ha", "tx_des_con": "condicao",
            "tx_tipo_im": "tipo_imovel",
        }),
    ]

    for tabela, layer, colunas in layers:
        try:
            n = sync_fast(tabela, layer, colunas)
            print(f"  OK: {n} registros\n")
        except Exception as e:
            print(f"  ERRO: {e}\n")

    print("Concluido!")
