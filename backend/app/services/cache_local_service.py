"""Consultas espaciais ao cache local PostGIS (GeoServer nacional unificado)."""

import logging
from typing import Any, Dict, List

from shapely.geometry import shape
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def _geojson_para_wkt(geojson: dict) -> str | None:
    if not geojson:
        return None
    try:
        return shape(geojson).wkt
    except Exception as e:
        logger.warning(f"GeoJSON para WKT: {e}")
        return None


async def _consulta_espacial(
    tabela: str,
    colunas: str,
    geojson: dict,
    filtro_extra: str = "",
    params_extra: dict | None = None,
    limite: int = 5,
) -> List[Dict[str, Any]]:
    wkt = _geojson_para_wkt(geojson)
    if not wkt:
        return []

    try:
        async with AsyncSessionLocal() as session:
            query = f"""
                SELECT {colunas},
                       ST_Area(ST_Intersection(geom, ST_GeomFromText(:wkt, 4326))::geography) / 10000 AS area_intersecao_ha
                FROM {tabela}
                WHERE ST_Intersects(geom, ST_GeomFromText(:wkt, 4326))
                {filtro_extra}
                ORDER BY area_intersecao_ha DESC
                LIMIT :limite
            """
            params: dict = {"wkt": wkt, "limite": limite}
            if params_extra:
                params.update(params_extra)

            result = await session.execute(text(query), params)
            return [dict(r._mapping) for r in result.fetchall()]
    except Exception as e:
        logger.warning(f"Cache {tabela}: {e}")
        return []


async def consultar_prodes_local(geojson: dict) -> list:
    return await _consulta_espacial("cache_prodes", "year, area_km, state, main_class, class_name, image_date", geojson, limite=500)


async def consultar_embargos_local(geojson: dict) -> list:
    return await _consulta_espacial("cache_embargos", "num_tad, orgao, data_embargo, area_ha, nome_infrator, cpf_cnpj, descricao", geojson, limite=20)


async def consultar_ti_local(geojson: dict) -> list:
    return await _consulta_espacial("cache_terras_indigenas", "nome_ti, etnia, fase, modalidade, municipio, orgao, area_ha", geojson, limite=5)


async def consultar_uc_local(geojson: dict) -> list:
    return await _consulta_espacial("cache_unidades_conservacao", "nome_uc, categoria, tipo, cod_cnuc, orgao, area_ha", geojson, limite=5)


async def consultar_quilombolas_local(geojson: dict) -> list:
    return await _consulta_espacial("cache_quilombolas", "nome, orgao, processo, area_ha", geojson, limite=5)


async def consultar_assentamentos_local(geojson: dict) -> list:
    return await _consulta_espacial("cache_assentamentos", "nome, orgao, codigo, familias, modalidade, area_ha", geojson, limite=5)


async def consultar_autos_infracao_local(geojson: dict) -> list:
    return await _consulta_espacial("cache_autos_infracao", "num_auto, data_lavratura, tipo_infracao, nome_infrator, cpf_cnpj, orgao", geojson, limite=10)


async def consultar_car_local(numero_car: str) -> list:
    """Busca um CAR pelo codigo no cache local e retorna geometria como GeoJSON."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT cod_imovel, status, nome_imovel, municipio, area_ha, condicao, tipo_imovel,
                           ST_AsGeoJSON(geom)::jsonb AS geometria_json,
                           SUBSTRING(cod_imovel FROM 1 FOR 2) AS estado
                    FROM cache_car_ativo
                    WHERE cod_imovel = :car
                    LIMIT 1
                """),
                {"car": numero_car},
            )
            rows = result.fetchall()
            return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.warning(f"Cache CAR {numero_car}: {e}")
        return []


async def consultar_car_geoserver(numero_car: str) -> dict | None:
    """Consulta o GeoServer nacional diretamente (WFS CQL) — fallback quando cache nao tem o CAR."""
    import httpx
    layers = ["vw_car", "vw_car_ativo", "vw_car_pendente", "vw_car_suspenso", "vw_car_cancelado"]
    for layer in layers:
        try:
            async with httpx.AsyncClient(timeout=15, verify=False) as client:
                resp = await client.get(
                    "https://geoserverdw.apps.geoapplications.net/geoserver/wfs/",
                    params={
                        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
                        "typeName": f"workspace_sicar:{layer}",
                        "CQL_FILTER": f"tx_cod_imovel='{numero_car}'",
                        "outputFormat": "application/json", "count": "1",
                    },
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                data = resp.json()
                feats = data.get("features", [])
                if feats:
                    props = feats[0].get("properties", {})
                    geom = feats[0].get("geometry")
                    return {
                        "estado": (props.get("tx_cod_imovel") or numero_car)[:2],
                        "municipio": props.get("tx_nome_municipio") or props.get("tx_nome_mu", ""),
                        "nome_imovel": props.get("tx_nome_imovel") or props.get("tx_nome_im", ""),
                        "area_ha": float(props.get("num_area_imovel") or props.get("num_area_i") or 0),
                        "status": props.get("tx_status_imovel") or props.get("tx_status_", "Pendente"),
                        "geometria": geom,
                    }
        except Exception:
            continue
    return None
