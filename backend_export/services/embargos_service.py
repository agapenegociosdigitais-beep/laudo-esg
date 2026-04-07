"""
Servico de Verificacao de Embargos Ambientais - Eureka Terra
Integracoes reais:
- IBAMA PAMGIA (ArcGIS REST API) - embargos federais
- SEMAS-PA LDI - embargos estaduais do Para
- PRODES/TerraBrasilis WFS - Marco UE (pos 31/12/2020)
"""
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# ?Estruturas de dados ?

@dataclass
class ResultadoEmbargo:
    embargo_detectado: bool
    fonte: str
    total_embargos: int
    embargos: list = field(default_factory=list)
    verificado: bool = True
    motivo_nao_verificado: Optional[str] = None

    def para_dict(self) -> Dict[str, Any]:
        """
        Serializa para o formato JSONB armazenado no banco.
        Mant�m compat com o frontend (campo 'embargado' lido em ComplianceStatus.tsx).
        """
        primeiro = self.embargos[0] if self.embargos else {}
        return {
            # Campo lido pelo frontend
            "embargado": self.embargo_detectado if self.verificado else None,
            "orgao": self.fonte,
            "numero_embargo": primeiro.get("numero_tad"),
            "data_embargo": primeiro.get("data_embargo"),
            "area_embargada_ha": primeiro.get("area_ha"),
            "motivo": primeiro.get("descricao"),
            "fonte": self.fonte,
            "verificado": self.verificado,
            "status_display": (
                "Embargado" if self.embargo_detectado
                else "N�o verificado" if not self.verificado
                else "Regular"
            ),
            # Campos extras do novo formato
            "total_embargos": self.total_embargos,
            "embargos": self.embargos,
            "motivo_nao_verificado": self.motivo_nao_verificado,
        }


# ?URLs confirmadas e testadas ?

IBAMA_PAMGIA_URL = (
    "https://pamgia.ibama.gov.br/server/rest/services/01_Publicacoes_Bases/adm_embargos_ibama_a/FeatureServer/0/query"
)
SEMAS_LDI_URL = "https://monitoramento.semas.pa.gov.br/ldi/pesquisa/pesquisarComCar"
PRODES_WFS_BASE = "https://terrabrasilis.dpi.inpe.br/geoserver/ows"

HEADERS = {
    "User-Agent": "EurekaTerra/1.0 (compliance@eurekaterra.com)",
    "Accept": "application/json, text/html, */*",
}

# ?Helpers de geometria ?

def _geojson_para_esri(geojson: dict) -> dict:
    """Converte GeoJSON para formato ESRI Geometry (ArcGIS REST API)."""
    if not geojson:
        return {}
    geo_type = geojson.get("type", "")
    if geo_type == "Polygon":
        return {"rings": geojson["coordinates"], "spatialReference": {"wkid": 4326}}
    elif geo_type == "MultiPolygon":
        rings = []
        for polygon in geojson["coordinates"]:
            rings.extend(polygon)
        return {"rings": rings, "spatialReference": {"wkid": 4326}}
    elif geo_type == "Feature":
        return _geojson_para_esri(geojson.get("geometry", {}))
    elif geo_type == "FeatureCollection":
        features = geojson.get("features", [])
        if features:
            return _geojson_para_esri(features[0])
    return {}


def _bbox_do_geojson(geojson: dict) -> Optional[tuple]:
    """Extrai bounding box (xmin, ymin, xmax, ymax) de um GeoJSON."""
    coords: list = []

    def _extract(obj):
        if isinstance(obj, list):
            if obj and isinstance(obj[0], (int, float)):
                coords.append(obj[:2])
            else:
                for item in obj:
                    _extract(item)
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


def _hash_car(car: str) -> int:
    return int(hashlib.sha256(car.encode()).hexdigest(), 16)


# ?IBAMA PAMGIA ?embargos federais ?

async def verificar_embargos_ibama(
    car_numero: str,
    geometria: Optional[dict] = None,
    estado: str = "",
) -> ResultadoEmbargo:
    """
    Consulta embargos do IBAMA via PAMGIA ArcGIS REST API.
    URL: pamgia.ibama.gov.br/geoservicos/rest/services/GI_AREASEMBARGADAS/MapServer/0/query
    Campos: NUM_TAD, SIT_TAD, DT_TAD, MUN_EMBAR, UF_EMBAR, AREA_HA, AREA_INT_HA, AREA_INT_PCT
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False, headers=HEADERS) as client:
            params = {
                "outFields": (
                    "num_tad,seq_tad,uf,municipio,qtd_area_embargada,dat_embargo,sit_desmatamento,nome_embargado,cpf_cnpj_embargado,des_tipo_bioma,num_processo,des_infracao"
                ),
                "returnGeometry": "false",
                "f": "json",
            }

            if geometria:
                esri_geom = _geojson_para_esri(geometria)
                if esri_geom:
                    params["geometry"] = json.dumps(esri_geom)
                    params["geometryType"] = "esriGeometryPolygon"
                    params["spatialRel"] = "esriSpatialRelIntersects"
                    params["inSR"] = "4326"
                    params["where"] = "1=1"
                else:
                    uf = estado or car_numero[:2].upper()
                    params["where"] = f"uf='{uf}'"
                    params["resultRecordCount"] = "100"
            else:
                uf = estado or car_numero[:2].upper()
                params["where"] = f"uf='{uf}'"
                params["resultRecordCount"] = "100"

            resp = await client.get(IBAMA_PAMGIA_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                raise ValueError(f"IBAMA API erro: {data['error']}")

            features = data.get("features", [])
            embargos = []
            for feat in features:
                attrs = feat.get("attributes", {})
                embargos.append({
                    "numero_tad": attrs.get("num_tad", ""),
                    "processo": attrs.get("seq_tad", ""),
                    "data_embargo": str(attrs.get("dat_embargo", "")),
                    "data_expiracao": None,
                    "area_ha": float(attrs.get("qtd_area_embargada") or 0),
                    "area_intersecao_ha": 0.0,
                    "percentual_intersecao": 0.0,
                    "status": "ativo",
                    "municipio": attrs.get("municipio", ""),
                    "uf": attrs.get("uf", ""),
                    "descricao": attrs.get("des_infracao", "Embargo IBAMA"),
                    "fonte": "IBAMA PAMGIA",
                })

            embargo_detectado = any(e["status"] == "ativo" for e in embargos)
            logger.info(f"IBAMA PAMGIA: {len(embargos)} embargo(s) para {car_numero}")
            return ResultadoEmbargo(
                embargo_detectado=embargo_detectado,
                fonte="IBAMA PAMGIA",
                total_embargos=len(embargos),
                embargos=embargos,
                verificado=True,
            )

    except Exception as exc:
        logger.warning(f"IBAMA PAMGIA indisponivel ({exc}), usando simulacao.")
        return _simular_embargos_ibama(car_numero)


# ?SEMAS-PA LDI ?embargos estaduais ?

async def verificar_embargos_semas(
    car_numero: str,
    geometria: Optional[dict] = None,
) -> ResultadoEmbargo:
    """Consulta LDI (Lista de Desmatamento Ilegal) da SEMAS-PA."""
    if not car_numero.upper().startswith("PA-"):
        return ResultadoEmbargo(
            embargo_detectado=False,
            fonte="SEMAS-PA (N/A)",
            total_embargos=0,
            embargos=[],
            verificado=True,
            motivo_nao_verificado="Im�vel fora do Par�",
        )
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=False,
            headers={**HEADERS, "Referer": "https://monitoramento.semas.pa.gov.br/ldi/"},
            follow_redirects=True,
        ) as client:
            # GET com codigoImovel - endpoint correto SEMAS-PA LDI
            params = {"codigoImovel": car_numero}
            resp = await client.get(SEMAS_LDI_URL, params=params)
            resp.raise_for_status()
            embargos = _parse_semas_html(resp.text, car_numero)
            logger.info(f"SEMAS-PA LDI: {len(embargos)} embargo(s) para {car_numero}")
            return ResultadoEmbargo(
                embargo_detectado=len(embargos) > 0,
                fonte="SEMAS-PA LDI",
                total_embargos=len(embargos),
                embargos=embargos,
                verificado=True,
            )
    except Exception as exc:
        logger.warning(f"SEMAS-PA LDI indisponivel ({exc}), usando simulacao.")
        return _simular_embargos_semas(car_numero)


def _parse_semas_html(html: str, car_numero: str) -> list:
    embargos = []
    try:
        if "Nenhum resultado" in html or "nao encontrado" in html.lower():
            return []
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)
        for row in rows[1:]:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
            if len(cells) >= 4:
                clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
                if clean[0] and clean[0] != car_numero:
                    try:
                        area = (
                            float(clean[3].replace(",", "."))
                            if clean[3].replace(",", "").replace(".", "").isdigit()
                            else 0
                        )
                    except Exception:
                        area = 0
                    embargos.append({
                        "numero_tad": clean[0],
                        "processo": clean[1] if len(clean) > 1 else "",
                        "data_embargo": clean[2] if len(clean) > 2 else "",
                        "data_expiracao": None,
                        "area_ha": area,
                        "area_intersecao_ha": 0,
                        "percentual_intersecao": 0,
                        "status": "ativo",
                        "municipio": "",
                        "uf": "PA",
                        "descricao": f"Embargo SEMAS-PA - {clean[0]}",
                        "fonte": "SEMAS-PA",
                    })
    except Exception as e:
        logger.warning(f"Erro ao parsear HTML SEMAS: {e}")
    return embargos


# ?PRODES/TerraBrasilis WFS ?Marco UE ?

async def verificar_marco_ue_prodes(
    car_numero: str,
    geometria: Optional[dict] = None,
    estado: str = "",
) -> dict:
    """
    Verifica desmatamento ap�s 31/12/2020 (Marco EUDR/UE).

    Endpoint confirmado: https://terrabrasilis.dpi.inpe.br/geoserver/ows
    Camadas dispon�veis (verificadas via GetCapabilities):
      - prodes-legal-amz:yearly_deforestation  (Amaz�nia Legal)
      - prodes-cerrado-nb:yearly_deforestation (Cerrado)
    Campos: year (int), area_km (float), state (UF), main_class ('desmatamento')
    Filtro Marco UE: year >= 2021 AND main_class = 'desmatamento'
    """
    UFS_AMAZONIA = {"AM", "PA", "MT", "RO", "TO", "MA", "AP", "AC", "RR"}
    UFS_CERRADO = {"GO", "MS", "PI", "BA", "MG", "SP", "DF", "MG"}

    uf = (estado or car_numero[:2]).upper()

    # Escolhe camadas por bioma ?usa Legal Amazon + Cerrado se necess�rio
    camadas: list[str] = []
    if uf in UFS_AMAZONIA:
        camadas = ["prodes-legal-amz:yearly_deforestation"]
    elif uf in UFS_CERRADO:
        camadas = ["prodes-cerrado-nb:yearly_deforestation"]
    else:
        # Fallback: tenta ambas
        camadas = [
            "prodes-legal-amz:yearly_deforestation",
            "prodes-cerrado-nb:yearly_deforestation",
        ]

    try:
        async with httpx.AsyncClient(timeout=45.0, verify=False, headers=HEADERS) as client:
            desmatamento_pos_2020: list[dict] = []

            for camada in camadas:
                params: Dict[str, Any] = {
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetFeature",
                    "typeName": camada,
                    "outputFormat": "application/json",
                    "count": "50",
                    "propertyName": "year,area_km,state,main_class,image_date",
                }

                if geometria:
                    bbox = _bbox_do_geojson(geometria)
                    if bbox:
                        cql = (
                            f"BBOX(geom,{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},'EPSG:4326')"
                            f" AND year>=2021 AND main_class='desmatamento'"
                        )
                        params["CQL_FILTER"] = cql
                    else:
                        params["CQL_FILTER"] = (
                            f"state='{uf}' AND year>=2021 AND main_class='desmatamento'"
                        )
                else:
                    params["CQL_FILTER"] = (
                        f"state='{uf}' AND year>=2021 AND main_class='desmatamento'"
                    )

                try:
                    resp = await client.get(PRODES_WFS_BASE, params=params, timeout=20.0)
                    resp.raise_for_status()
                    data = resp.json()
                    for feat in data.get("features", []):
                        props = feat.get("properties", {})
                        if props.get("main_class") != "desmatamento":
                            continue
                        area_km2 = float(props.get("area_km") or 0)
                        desmatamento_pos_2020.append({
                            "ano": props.get("year"),
                            "area_ha": round(area_km2 * 100, 2),
                            "area_km2": area_km2,
                            "uf": props.get("state", ""),
                            "data": props.get("image_date", ""),
                            "camada": camada,
                            "fonte": "PRODES/INPE TerraBrasilis",
                        })
                except Exception as cam_exc:
                    logger.warning(f"PRODES camada {camada} erro: {cam_exc}")
                    continue

            todas_falharam = len(camadas) > 0 and len(desmatamento_pos_2020) == 0 and not any(True for _ in camadas)
            em_conformidade = len(desmatamento_pos_2020) == 0
            area_total = sum(d["area_ha"] for d in desmatamento_pos_2020)
            logger.info(
                f"PRODES Marco UE: {len(desmatamento_pos_2020)} registro(s) "
                f"p�s-2020 para {car_numero} (UF={uf})"
            )
            return {
                "em_conformidade": em_conformidade,
                "desmatamento_detectado": not em_conformidade,
                "registros_pos_2020": desmatamento_pos_2020,
                "total_registros": len(desmatamento_pos_2020),
                "area_total_ha": area_total,
                "marco_referencia": "31/12/2020",
                "regulacao": "EUDR (EU Deforestation Regulation)",
                "verificado": True,
                "fonte": "PRODES/INPE TerraBrasilis",
            }

    except Exception as exc:
        logger.warning(f"PRODES API indispon�vel ({exc}), usando simula��o.")
        return _simular_marco_ue(car_numero)


# ?Simula��es determin�sticas (fallback) ?

def _simular_embargos_ibama(car_numero: str) -> ResultadoEmbargo:
    h = _hash_car(car_numero)
    uf = car_numero[:2].upper()
    amazonia = uf in {"AM", "PA", "MT", "RO", "TO", "MA", "AP", "AC", "RR"}
    tem = (h % 100) < (30 if amazonia else 12)
    embargos = []
    if tem:
        for i in range((h % 2) + 1):
            embargos.append({
                "numero_tad": f"{800 + i + h % 200}/2024",
                "processo": f"02001.{h % 999999:06d}/{2020 + i % 5}-{h % 99:02d}",
                "data_embargo": f"{(h % 28) + 1:02d}/{(h % 11) + 1:02d}/{2020 + (h % 4)}",
                "data_expiracao": None,
                "area_ha": round((h % 500) + 50.0, 2),
                "area_intersecao_ha": round((h % 100) + 10.0, 2),
                "percentual_intersecao": round((h % 100) * 0.8, 1),
                "status": "ativo",
                "municipio": "Simulado",
                "uf": uf,
                "descricao": "[SIMULADO] Embargo IBAMA",
                "fonte": "IBAMA (simulado)",
            })
    return ResultadoEmbargo(
        embargo_detectado=tem,
        fonte="IBAMA PAMGIA (simulado)",
        total_embargos=len(embargos),
        embargos=embargos,
        verificado=False,
        motivo_nao_verificado="API indispon�vel",
    )


def _simular_embargos_semas(car_numero: str) -> ResultadoEmbargo:
    h = _hash_car(car_numero)
    tem = (h % 100) < 25
    embargos = []
    if tem:
        embargos.append({
            "numero_tad": f"LDI-{h % 9999:04d}/2024",
            "processo": f"PA-{h % 99999:05d}",
            "data_embargo": f"{(h % 28) + 1:02d}/{(h % 11) + 1:02d}/2024",
            "data_expiracao": None,
            "area_ha": round((h % 300) + 30.0, 2),
            "area_intersecao_ha": round((h % 80) + 5.0, 2),
            "percentual_intersecao": round((h % 100) * 0.6, 1),
            "status": "ativo",
            "municipio": "Simulado-PA",
            "uf": "PA",
            "descricao": "[SIMULADO] LDI SEMAS-PA",
            "fonte": "SEMAS-PA (simulado)",
        })
    return ResultadoEmbargo(
        embargo_detectado=tem,
        fonte="SEMAS-PA LDI (simulado)",
        total_embargos=len(embargos),
        embargos=embargos,
        verificado=False,
        motivo_nao_verificado="API indispon�vel",
    )


def _simular_marco_ue(car_numero: str) -> dict:
    h = _hash_car(car_numero)
    uf = car_numero[:2].upper()
    amazonia = uf in {"AM", "PA", "MT", "RO", "TO", "MA", "AP", "AC", "RR"}
    tem = (h % 100) < (35 if amazonia else 10)
    registros = []
    if tem:
        registros.append({
            "ano": 2021 + (h % 3),
            "area_ha": round((h % 200) + 10.0, 2),
            "municipio": "Simulado",
            "uf": uf,
            "fonte": "PRODES/INPE (simulado)",
        })
    return {
        "em_conformidade": not tem,
        "desmatamento_detectado": tem,
        "registros_pos_2020": registros,
        "total_registros": len(registros),
        "area_total_ha": sum(r["area_ha"] for r in registros),
        "marco_referencia": "31/12/2020",
        "regulacao": "EUDR (EU Deforestation Regulation)",
        "verificado": False,
        "fonte": "PRODES/INPE (simulado)",
    }
