"""
Serviço SICAR — busca geometria e dados reais de CAR
via GeoServer público do SICAR (sem captcha, sem autenticação).
Endpoint: https://geoserver.car.gov.br/geoserver/sicar/wfs
"""
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

SICAR_WFS = "https://geoserver.car.gov.br/geoserver/sicar/wfs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

LAYER_POR_UF = {
    "AC": "sicar:sicar_imoveis_ac", "AL": "sicar:sicar_imoveis_al",
    "AM": "sicar:sicar_imoveis_am", "AP": "sicar:sicar_imoveis_ap",
    "BA": "sicar:sicar_imoveis_ba", "CE": "sicar:sicar_imoveis_ce",
    "DF": "sicar:sicar_imoveis_df", "ES": "sicar:sicar_imoveis_es",
    "GO": "sicar:sicar_imoveis_go", "MA": "sicar:sicar_imoveis_ma",
    "MG": "sicar:sicar_imoveis_mg", "MS": "sicar:sicar_imoveis_ms",
    "MT": "sicar:sicar_imoveis_mt", "PA": "sicar:sicar_imoveis_pa",
    "PB": "sicar:sicar_imoveis_pb", "PE": "sicar:sicar_imoveis_pe",
    "PI": "sicar:sicar_imoveis_pi", "PR": "sicar:sicar_imoveis_pr",
    "RJ": "sicar:sicar_imoveis_rj", "RN": "sicar:sicar_imoveis_rn",
    "RO": "sicar:sicar_imoveis_ro", "RR": "sicar:sicar_imoveis_rr",
    "RS": "sicar:sicar_imoveis_rs", "SC": "sicar:sicar_imoveis_sc",
    "SE": "sicar:sicar_imoveis_se", "SP": "sicar:sicar_imoveis_sp",
    "TO": "sicar:sicar_imoveis_to",
}

STATUS_MAP = {
    "AT": "Ativo", "PE": "Pendente",
    "CA": "Cancelado", "SU": "Suspenso",
    "IN": "Inscrito", "RE": "Retificado",
}

TIPO_MAP = {
    "IRU": "Imóvel Rural",
    "PCT": "Povos e Comunidades Tradicionais",
    "AST": "Assentamento Reforma Agrária",
}


async def buscar_car_sicar(car_numero: str) -> dict:
    """
    Busca dados e geometria real de um CAR no SICAR via WFS público.
    Retorna dict com sucesso, dados da propriedade e geometria GeoJSON.
    """
    uf = car_numero[:2].upper()
    layer = LAYER_POR_UF.get(uf)

    if not layer:
        logger.warning(f"UF {uf} nao suportada no SICAR WFS")
        return {
            "sucesso": False,
            "erro": f"Estado {uf} nao suportado",
            "car": car_numero,
        }

    try:
        async with httpx.AsyncClient(
            timeout=30, verify=False, headers=HEADERS
        ) as client:
            resp = await client.get(SICAR_WFS, params={
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": layer,
                "CQL_FILTER": f"cod_imovel='{car_numero}'",
                "outputFormat": "application/json",
                "count": 1,
            })
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])

            if not features:
                logger.warning(f"CAR {car_numero} nao encontrado no SICAR")
                return {
                    "sucesso": False,
                    "erro": "CAR nao encontrado no SICAR",
                    "car": car_numero,
                }

            feature = features[0]
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})

            status_cod = props.get("status_imovel") or ""
            tipo_cod = props.get("tipo_imovel", "")
            status_descritivo = STATUS_MAP.get(status_cod) or ("Não informado" if not status_cod else status_cod)

            resultado = {
                "sucesso": True,
                "car": car_numero,
                "cod_imovel": props.get("cod_imovel", car_numero),
                "status_codigo": status_cod,
                "status": status_descritivo,
                "situacao_car": status_descritivo,
                "area_ha": props.get("area", 0),
                "area_total_ha": props.get("area", 0),
                "municipio": props.get("municipio", ""),
                "uf": props.get("uf", uf),
                "condicao": props.get("condicao", ""),
                "tipo_codigo": tipo_cod,
                "tipo": TIPO_MAP.get(tipo_cod, tipo_cod),
                "modulos_fiscais": props.get("m_fiscal", 0),
                "data_criacao": props.get("dat_criacao", ""),
                "data_atualizacao": props.get("data_atualizacao", ""),
                "cod_municipio_ibge": props.get("cod_municipio_ibge", ""),
                "geometria": geom,
                "fonte": "SICAR/GeoServer",
            }

            logger.info(
                f"SICAR: CAR {car_numero} encontrado — "
                f"{resultado['municipio']}/{resultado['uf']} "
                f"{resultado['area_ha']} ha [{resultado['status']}]"
            )
            return resultado

    except httpx.TimeoutException:
        logger.error(f"SICAR timeout para {car_numero}")
        return {"sucesso": False, "erro": "Timeout SICAR", "car": car_numero}
    except Exception as e:
        logger.error(f"SICAR erro para {car_numero}: {e}")
        return {"sucesso": False, "erro": str(e), "car": car_numero}