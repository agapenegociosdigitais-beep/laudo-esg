"""
Servico de Conformidade Socioambiental - Eureka Terra
Criterios baseados no Protocolo de Monitoramento de Fornecedores de Gado da Amazonia
Inclui verificacoes para pecuaria E soja (dupla conformidade)
"""
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "EurekaTerra/1.0 (compliance@eurekaterra.com)",
    "Accept": "application/json, text/html, */*",
}

INCRA_WFS = "https://cmr.funai.gov.br/geoserver/wfs"
MTE_URL = "https://transparencia.gov.br/api-de-dados/trabalho-escravo/lista-suja"


def _bbox_geojson(geojson: dict) -> Optional[tuple]:
    coords = []
    def _extract(obj):
        if isinstance(obj, list):
            if obj and isinstance(obj[0], (int, float)):
                coords.append(obj[:2])
            else:
                for i in obj:
                    _extract(i)
        elif isinstance(obj, dict):
            t = obj.get("type", "")
            if t == "Feature":
                _extract(obj.get("geometry", {}))
            elif t == "FeatureCollection":
                for f in obj.get("features", []):
                    _extract(f)
            else:
                _extract(obj.get("coordinates", []))
    _extract(geojson)
    if not coords:
        return None
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return (min(xs), min(ys), max(xs), max(ys))


async def _consultar_wfs(
    client: httpx.AsyncClient,
    url: str,
    typename: str,
    bbox: Optional[tuple] = None,
    cql_filter: Optional[str] = None,
    max_features: int = 20,
    version: str = "2.0.0",
) -> list:
    params = {
        "service": "WFS",
        "version": version,
        "request": "GetFeature",
        "typeName": typename,
        "outputFormat": "application/json",
    }
    if version == "2.0.0":
        params["count"] = str(max_features)
    else:
        params["maxFeatures"] = str(max_features)
    if bbox:
        params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326"
    if cql_filter:
        params["CQL_FILTER"] = cql_filter
    try:
        r = await client.get(url, params=params, timeout=15.0)
        r.raise_for_status()
        data = r.json()
        return data.get("features", [])
    except Exception as e:
        logger.warning(f"WFS {typename} erro: {e}")
        return []


async def verificar_quilombolas(
    car_numero: str,
    geometria: Optional[dict] = None,
    estado: str = "",
) -> dict:
    # ── 1. Cache local ──────────────────────────────────────────────────────
    if geometria:
        try:
            from app.services.cache_local_service import consultar_quilombolas_local
            local = await consultar_quilombolas_local(geometria)
            if local:
                nomes = [r.get("nome", "") for r in local[:3] if r.get("nome")]
                return {
                    "sobreposicao": True,
                    "total": len(local),
                    "nomes": nomes,
                    "verificado": True,
                    "fonte": "GeoServer Nacional (cache)",
                }
            return {
                "sobreposicao": False,
                "total": 0,
                "nomes": [],
                "verificado": True,
                "fonte": "INCRA (cache local)",
            }
        except Exception as e:
            logger.warning(f"Cache quilombolas indisponível: {e}")

    # ── 2. API ao vivo ──────────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=False, headers=HEADERS) as client:
            bbox = _bbox_geojson(geometria) if geometria else None
            uf = estado or car_numero[:2].upper()
            cql = None if bbox else f"uf='{uf}'"
            feats = await _consultar_wfs(
                client, INCRA_WFS,
                "CMR-PUBLICO:lim_quilombolas_a",
                bbox=bbox, cql_filter=cql,
            )
            sobreposicao = len(feats) > 0
            nomes = [f.get("properties", {}).get("nm_comunid", "") for f in feats[:3]]
            logger.info(f"Quilombolas: {len(feats)} para {car_numero}")
            return {
                "sobreposicao": sobreposicao,
                "total": len(feats),
                "nomes": [n for n in nomes if n],
                "verificado": True,
                "fonte": "INCRA",
            }
    except Exception as e:
        logger.warning(f"INCRA Quilombolas erro: {e}")
        return {
            "sobreposicao": False,
            "total": 0,
            "nomes": [],
            "verificado": False,
            "fonte": f"INCRA (erro: {str(e)[:80]})",
        }


async def verificar_assentamentos(
    car_numero: str,
    geometria: Optional[dict] = None,
    estado: str = "",
) -> dict:
    # ── 1. Cache local ──────────────────────────────────────────────────────
    if geometria:
        try:
            from app.services.cache_local_service import consultar_assentamentos_local
            local = await consultar_assentamentos_local(geometria)
            if local:
                detalhes = []
                for r in local[:5]:
                    det = r.get("nome", "")
                    if r.get("codigo"):
                        det += f" ({r.get('codigo')})"
                    if r.get("familias"):
                        det += f" - {r.get('familias')} familias"
                    if det:
                        detalhes.append(det)
                return {
                    "sobreposicao": True,
                    "total": len(local),
                    "nomes": detalhes,
                    "verificado": True,
                    "fonte": "GeoServer Nacional (cache)",
                }
            return {
                "sobreposicao": False,
                "total": 0,
                "nomes": [],
                "verificado": True,
                "fonte": "INCRA (cache local)",
            }
        except Exception as e:
            logger.warning(f"Cache assentamentos indisponível: {e}")

    # ── 2. API ao vivo ──────────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=False, headers=HEADERS) as client:
            bbox = _bbox_geojson(geometria) if geometria else None
            uf = estado or car_numero[:2].upper()
            cql = None if bbox else f"uf_pa='{uf}'"
            feats = await _consultar_wfs(
                client, INCRA_WFS,
                "CMR-PUBLICO:lim_assentamento_rural_a",
                bbox=bbox, cql_filter=cql,
            )
            sobreposicao = len(feats) > 0
            nomes = []
            for f in feats[:5]:
                props = f.get("properties", {})
                nome = props.get("no_projeto", "") or props.get("nome", "") or props.get("nom_proje", "")
                municipio = props.get("no_municipio", "") or props.get("municipio", "")
                sipra = props.get("cd_sipra", "") or props.get("sipra", "")
                partes = [p for p in [nome, municipio, f"SIPRA {sipra}" if sipra else ""] if p]
                if partes:
                    nomes.append(" - ".join(partes))
            logger.info(f"Assentamentos: {len(feats)} para {car_numero}")
            return {
                "sobreposicao": sobreposicao,
                "total": len(feats),
                "nomes": nomes,
                "verificado": True,
                "fonte": "INCRA",
            }
    except Exception as e:
        logger.warning(f"INCRA Assentamentos erro: {e}")
        return {
            "sobreposicao": False,
            "total": 0,
            "nomes": [],
            "verificado": False,
            "fonte": f"INCRA (erro: {str(e)[:80]})",
        }


async def verificar_trabalho_escravo(
    car_numero: str,
    cpf_cnpj: Optional[str] = None,
    nome_proprietario: Optional[str] = None,
) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False, headers=HEADERS) as client:
            pagina = 1
            encontrado = False
            nome_encontrado = ""
            while pagina <= 5:
                r = await client.get(
                    MTE_URL,
                    params={"pagina": pagina, "tamanhoPagina": 100},
                    timeout=10.0,
                )
                if r.status_code != 200:
                    break
                registros = r.json()
                if not registros:
                    break
                for reg in registros:
                    cnpj_reg = re.sub(r"\D", "", str(reg.get("cnpjCpfEmpregador", "")))
                    nome_reg = str(reg.get("nomeEmpregador", "")).upper()
                    if cpf_cnpj:
                        cnpj_limpo = re.sub(r"\D", "", cpf_cnpj)
                        if cnpj_limpo and cnpj_limpo == cnpj_reg:
                            encontrado = True
                            nome_encontrado = reg.get("nomeEmpregador", "")
                            break
                    if nome_proprietario:
                        nome_upper = nome_proprietario.upper()
                        if len(nome_upper) > 5 and nome_upper in nome_reg:
                            encontrado = True
                            nome_encontrado = reg.get("nomeEmpregador", "")
                            break
                if encontrado:
                    break
                pagina += 1
            return {
                "trabalho_escravo": encontrado,
                "nome_encontrado": nome_encontrado,
                "verificado": True,
                "fonte": "Portal da Transparencia / MTE",
            }
    except Exception as e:
        logger.warning(f"MTE Lista Suja indisponivel: {e}")
        return {
            "trabalho_escravo": False,
            "verificado": False,
            "fonte": f"MTE (erro: {str(e)[:80]})",
        }


def calcular_balanco_ambiental(
    area_total_ha: float,
    area_veg_nativa_ha: float,
    area_app_ha: float,
    area_rl_ha: float,
    area_consolidada_ha: float,
    bioma: str,
) -> dict:
    pct_rl = 0.80 if "Amazonia" in bioma else 0.20
    rl_exigida = round(area_total_ha * pct_rl, 2)
    excedente_rl = max(0.0, round(area_rl_ha - rl_exigida, 2))
    deficit_rl = max(0.0, round(rl_exigida - area_rl_ha, 2))
    app_necessaria = round(area_total_ha * 0.08, 2)
    deficit_app = max(0.0, round(app_necessaria - area_app_ha, 2))
    return {
        "rl_exigida_ha": rl_exigida,
        "rl_existente_ha": area_rl_ha,
        "excedente_rl_ha": excedente_rl,
        "deficit_rl_ha": deficit_rl,
        "app_necessaria_ha": app_necessaria,
        "app_declarada_ha": area_app_ha,
        "deficit_app_ha": deficit_app,
        "em_conformidade": deficit_rl == 0 and deficit_app == 0,
        "percentual_rl_exigida": int(pct_rl * 100),
    }
