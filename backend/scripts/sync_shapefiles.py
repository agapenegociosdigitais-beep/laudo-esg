#!/usr/bin/env python3
"""
Sincroniza dados do GeoServer nacional unificado para o PostGIS local.
Fonte: https://geoserverdw.apps.geoapplications.net/geoserver/wfs/

Uso: python scripts/sync_shapefiles.py
"""

import logging
import os
import shutil
import sys
import tempfile
import time
import zipfile
from io import BytesIO
from pathlib import Path

import geopandas as gpd
import httpx
import sqlalchemy as sa
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

DB_URL = os.getenv("DATABASE_URL", "postgresql://eureka:eurekapass@eureka_postgres:5432/eureka_db")
GEO_URL = "https://geoserverdw.apps.geoapplications.net/geoserver/wfs/"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("sync")

engine = sa.create_engine(DB_URL.replace("+asyncpg", "+psycopg2"))


def log_sync(tabela: str, registros: int, erros: int, duracao: float):
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO cache_sync_log (tabela, registros_importados, erros, duracao_segundos)
                VALUES (:t, :r, :e, :d)
            """), {"t": tabela, "r": registros, "e": erros, "d": round(duracao, 2)})
    except Exception:
        pass


def baixar_zip(layer: str) -> BytesIO:
    resp = httpx.get(GEO_URL, params={
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeName": layer, "outputFormat": "SHAPE-ZIP",
    }, headers=HEADERS, timeout=600, verify=False)
    resp.raise_for_status()
    return BytesIO(resp.content)


def importar_zip(zip_data: BytesIO, tabela: str, colunas: dict, srid: int = 4326) -> int:
    """Extrai shapefile ZIP e importa via WKB (ST_GeomFromWKB)."""
    tmpdir = tempfile.mkdtemp(prefix="sync_")
    try:
        with zipfile.ZipFile(zip_data) as zf:
            zf.extractall(tmpdir)

        shp_files = [f for f in os.listdir(tmpdir) if f.lower().endswith(".shp")]
        if not shp_files:
            raise ValueError(f"Nenhum .shp em {tabela}")
        shp_path = Path(tmpdir) / shp_files[0]

        gdf = gpd.read_file(shp_path)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=srid)
        elif gdf.crs.to_epsg() != srid:
            gdf = gdf.to_crs(epsg=srid)

        colunas_validas = {k: v for k, v in colunas.items() if k in gdf.columns}
        gdf = gdf.rename(columns=colunas_validas)
        gdf = gdf.set_geometry("geometry")

        # Drop e recria
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {tabela} CASCADE"))
            cols_ddl = ", ".join(f"{dest} TEXT" for dest in colunas_validas.values())
            conn.execute(text(f"CREATE TABLE {tabela} ({cols_ddl})"))
            conn.execute(text(f"SELECT AddGeometryColumn('public', '{tabela}', 'geom', {srid}, 'MULTIPOLYGON', 2)"))
            conn.execute(text(f"CREATE INDEX idx_{tabela}_geom ON {tabela} USING GIST (geom)"))

        # Insere em lotes
        cols_dest = list(colunas_validas.values())
        total = 0
        batch = 2000

        for i in range(0, len(gdf), batch):
            chunk = gdf.iloc[i:i+batch]
            with engine.begin() as conn:
                for _, row in chunk.iterrows():
                    wkt = row.geometry.wkt
                    vals = {}
                    for c in cols_dest:
                        v = row.get(c)
                        if v is not None and str(v) not in ('nan', 'None', ''):
                            vals[c] = str(v)[:5000]
                    if not vals:
                        conn.execute(text(f"INSERT INTO {tabela} (geom) VALUES (ST_Multi(ST_Force2D(ST_GeomFromText(:w, {srid}))))"), {"w": wkt})
                    else:
                        cols = list(vals.keys())
                        ph = ", ".join(f":{c}" for c in cols)
                        conn.execute(text(
                            f"INSERT INTO {tabela} ({', '.join(cols)}, geom) "
                            f"VALUES ({ph}, ST_Multi(ST_Force2D(ST_GeomFromText(:__w, {srid}))))"
                        ), {**vals, "__w": wkt})
            total += len(chunk)
            logger.info(f"  {tabela}: {total}/{len(gdf)}")

        return total
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ════════════════════════════════════════════════════════════════════════

def sync_embargos() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_sicar_embargos"), "cache_embargos", {
        "tx_num_tad": "num_tad", "tx_seq_tad": "seq_tad", "tx_orgao_resp": "orgao",
        "dat_embargo": "data_embargo", "area_embargo_ha": "area_ha",
        "tx_nome_infrator": "nome_infrator", "tx_cpf_cnpj": "cpf_cnpj",
        "tx_descricao_condicao": "descricao", "sit_desembargo": "situacao",
    })

def sync_ti() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_sicar_terras_indigenas"), "cache_terras_indigenas", {
        "tx_nome": "nome_ti", "tx_etnia": "etnia", "tx_fase": "fase",
        "tx_modalidade": "modalidade", "tx_nome_municipio": "municipio",
        "tx_orgao_resp": "orgao", "area_ti_ha": "area_ha",
    })

def sync_uc() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_sicar_unidades_conservacao"), "cache_unidades_conservacao", {
        "tx_nome": "nome_uc", "tx_categoria": "categoria", "tx_tipo": "tipo",
        "num_cod_cnuc": "cod_cnuc", "num_ano_criacao": "ano_criacao",
        "tx_orgao_resp": "orgao", "area_uc_ha": "area_ha",
    })

def sync_quilombolas() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_sicar_areas_quilombolas"), "cache_quilombolas", {
        "tx_nome": "nome", "tx_orgao_resp": "orgao", "tx_processo": "processo",
        "area_quilombola_ha": "area_ha",
    })

def sync_assentamentos() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_sicar_assentamentos"), "cache_assentamentos", {
        "tx_nome": "nome", "tx_orgao_resp": "orgao", "cod_assentamento": "codigo",
        "num_familia": "familias", "tx_modalidade": "modalidade",
        "area_assentamento_ha": "area_ha",
    })

def sync_prodes() -> int:
    return importar_zip(baixar_zip("workspace_sicar:mv_desmatamento_prodes_2008"), "cache_prodes", {
        "year": "year", "area_km": "area_km", "state": "state",
        "main_class": "main_class", "class_name": "class_name",
        "image_date": "image_date", "path_row": "path_row",
    })

def sync_autos_infracao() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_sicar_autos_de_infracao"), "cache_autos_infracao", {
        "tx_num_auto": "num_auto", "dat_lavratura": "data_lavratura",
        "tx_tipo_infracao": "tipo_infracao", "tx_nome_infrator": "nome_infrator",
        "tx_cpf_cnpj": "cpf_cnpj", "tx_orgao_resp": "orgao",
    })

def sync_florestas_publicas() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_florestas_publicas_2024"), "cache_florestas_publicas", {
        "tx_nome": "nome", "tx_classe": "classe", "tx_categoria": "categoria",
        "tx_orgao_resp": "orgao", "area_florestas_publicas_ha": "area_ha",
    })

def sync_deter() -> int:
    return importar_zip(baixar_zip("workspace_fiscalizacao_inteligente:vw_alertas_deter"), "cache_alertas_deter", {
        "tx_classe_alerta": "classe_alerta", "dat_alerta": "data_alerta",
        "ano_alerta": "ano", "tx_sigla_uf": "uf", "area_calc_alerta": "area_ha",
    })

def sync_car_ativo() -> int:
    return importar_zip(baixar_zip("workspace_sicar:vw_car_ativo"), "cache_car_ativo", {
        # Nomes truncados (shapefile DBF limita a 10 chars)
        "tx_cod_imo": "cod_imovel", "tx_status_": "status",
        "tx_nome_im": "nome_imovel", "tx_nome_pr": "nome_proprietario",
        "tx_cpf_cnp": "cpf_cnpj", "tx_nome_mu": "municipio",
        "num_area_i": "area_ha", "tx_des_con": "condicao",
        "tx_tipo_im": "tipo_imovel",
    })


FONTES = [
    ("cache_embargos", sync_embargos),
    ("cache_terras_indigenas", sync_ti),
    ("cache_unidades_conservacao", sync_uc),
    ("cache_quilombolas", sync_quilombolas),
    ("cache_assentamentos", sync_assentamentos),
    ("cache_prodes", sync_prodes),
    ("cache_autos_infracao", sync_autos_infracao),
    ("cache_florestas_publicas", sync_florestas_publicas),
    ("cache_alertas_deter", sync_deter),
    ("cache_car_ativo", sync_car_ativo),
]


def main():
    logger.info("=" * 60)
    logger.info("Sincronizacao - GeoServer Nacional Unificado")
    logger.info("=" * 60)

    total_registros = 0
    falhas = 0

    for tabela, func in FONTES:
        logger.info(f"\n-- {tabela}")
        inicio = time.time()
        try:
            n = func()
            duracao = time.time() - inicio
            log_sync(tabela, n, 0, duracao)
            total_registros += n
            logger.info(f"  OK: {n} registros em {duracao:.1f}s")
        except Exception as e:
            duracao = time.time() - inicio
            log_sync(tabela, 0, 1, duracao)
            falhas += 1
            logger.error(f"  ERRO: {e}")
            import traceback
            traceback.print_exc()

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Concluido: {total_registros} registros, {falhas} falhas")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
