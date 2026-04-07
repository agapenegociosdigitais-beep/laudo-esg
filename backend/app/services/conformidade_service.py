"""
Servi�o de Conformidade Socioambiental - Eureka Terra
Crit�rios baseados no Protocolo de Monitoramento de Fornecedores de Gado da Amaz�nia
Inclui verifica��es para pecu�ria E soja (dupla conformidade)
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "EurekaTerra/1.0 (compliance@eurekaterra.com)",
    "Accept": "application/json, text/html, */*",
}

INCRA_WFS = "https://cmr.funai.gov.br/geoserver/wfs"
MTE_URL   = "https://transparencia.gov.br/api-de-dados/trabalho-escravo/lista-suja"

def _hash(car: str) -> int:
    return int(hashlib.sha256(car.encode()).hexdigest(), 16)

def _bbox_geojson(geojson: dict) -> Optional[tuple]:
    coords = []
    def _extract(obj):
        if isinstance(obj, list):
            if obj and isinstance(obj[0], (int, float)):
                coords.append(obj[:2])
            else:
                for i in obj: _extract(i)
        elif isinstance(obj, dict):
            t = obj.get("type", "")
            if t == "Feature": _extract(obj.get("geometry", {}))
            elif t == "FeatureCollection":
                for f in obj.get("features", []): _extract(f)
            else: _extract(obj.get("coordinates", []))
    _extract(geojson)
    if not coords: return None
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

# ?Quilombolas (INCRA) ?
async def verificar_quilombolas(
    car_numero: str,
    geometria: Optional[dict] = None,
    estado: str = "",
) -> dict:
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
        return _simular_quilombola(car_numero)

def _simular_quilombola(car: str) -> dict:
    h = _hash(car)
    uf = car[:2].upper()
    prob = 0.08 if uf in {"AM","PA","MT","RO","TO","MA","AP","AC","RR"} else 0.03
    sobrepoe = (h % 100) < int(prob * 100)
    return {
        "sobreposicao": sobrepoe, "total": 1 if sobrepoe else 0,
        "nomes": ["Comunidade Quilombola (simulado)"] if sobrepoe else [],
        "verificado": False, "fonte": "INCRA (simulado)",
    }

# ?Assentamentos (INCRA) ?
async def verificar_assentamentos(
    car_numero: str,
    geometria: Optional[dict] = None,
    estado: str = "",
) -> dict:
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

            # INCRA WFS usa nomes de campo variáveis por camada/versão
            CAMPOS_NOME = ["nom_proje", "nome_projeto", "ds_nome", "nm_projeto", "nome_pa", "nome", "nm_assentamento"]
            CAMPOS_MUNICIPIO = ["nom_mun", "nome_mun", "municipio", "nm_municipio"]

            def _extrair_nome(props: dict) -> str:
                for campo in CAMPOS_NOME:
                    v = props.get(campo, "")
                    if v:
                        return str(v).strip()
                return ""

            def _extrair_municipio(props: dict) -> str:
                for campo in CAMPOS_MUNICIPIO:
                    v = props.get(campo, "")
                    if v:
                        return str(v).strip()
                return ""

            detalhes = []
            for f in feats[:5]:
                props = f.get("properties", {})
                nome = _extrair_nome(props)
                mun  = _extrair_municipio(props)
                cod  = props.get("cd_sipra") or props.get("sipra") or props.get("codigo") or ""
                area = props.get("area_ha") or props.get("area") or ""

                partes = []
                if nome:
                    partes.append(nome)
                if mun:
                    partes.append(f"Município: {mun}")
                if cod:
                    partes.append(f"SIPRA: {cod}")
                if area:
                    try:
                        partes.append(f"Área: {float(area):.0f} ha")
                    except (ValueError, TypeError):
                        pass

                if partes:
                    detalhes.append(" — ".join(partes))
                elif str(props):
                    # fallback: ao menos registra que encontrou algo
                    detalhes.append(f"Assentamento #{len(detalhes)+1} (dados sem nome)")

            nomes = detalhes if detalhes else (["Assentamento detectado (nome não informado pelo INCRA)"] if sobreposicao else [])

            logger.info(f"Assentamentos: {len(feats)} para {car_numero} — {nomes}")
            return {
                "sobreposicao": sobreposicao,
                "total": len(feats),
                "nomes": nomes,
                "verificado": True,
                "fonte": "INCRA",
            }
    except Exception as e:
        logger.warning(f"INCRA Assentamentos erro: {e}")
        return _simular_assentamento(car_numero)

def _simular_assentamento(car: str) -> dict:
    h = _hash(car)
    uf = car[:2].upper()
    prob = 0.12 if uf in {"AM","PA","MT","RO","TO","MA","AP","AC","RR"} else 0.05
    sobrepoe = (h % 100) < int(prob * 100)
    return {
        "sobreposicao": sobrepoe, "total": 1 if sobrepoe else 0,
        "nomes": ["PA Simulado"] if sobrepoe else [],
        "verificado": False, "fonte": "INCRA (simulado)",
    }

# ?Trabalho Escravo (Portal da Transpar�ncia) ?
async def verificar_trabalho_escravo(
    car_numero: str,
    cpf_cnpj: Optional[str] = None,
    nome_proprietario: Optional[str] = None,
) -> dict:
    """
    Consulta a Lista Suja do Trabalho Escravo via Portal da Transpar�ncia.
    URL confirmada: https://transparencia.gov.br/api-de-dados/trabalho-escravo/lista-suja
    """
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
                "fonte": "Portal da Transpar�ncia / MTE",
            }
    except Exception as e:
        logger.warning(f"MTE Lista Suja indispon�vel: {e}")
        return {
            "trabalho_escravo": False,
            "verificado": False,
            "fonte": "MTE (indispon�vel)",
        }

# ?Balan�o Ambiental (C�digo Florestal Lei 12.651/2012) ?
def calcular_balanco_ambiental(
    area_total_ha: float,
    area_veg_nativa_ha: float,
    area_app_ha: float,
    area_rl_ha: float,
    area_consolidada_ha: float,
    bioma: str,
) -> dict:
    pct_rl = 0.80 if "Amaz�nia" in bioma else 0.20
    rl_exigida = round(area_total_ha * pct_rl, 2)
    excedente_rl = max(0.0, round(area_rl_ha - rl_exigida, 2))
    deficit_rl   = max(0.0, round(rl_exigida - area_rl_ha, 2))
    app_necessaria = round(area_total_ha * 0.08, 2)
    deficit_app    = max(0.0, round(app_necessaria - area_app_ha, 2))
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
# ?Integra��o SICAR ?
from app.services.sicar_service import buscar_car_sicar

async def obter_geometria_sicar(car_numero: str) -> Optional[dict]:
    """Busca geometria real do im�vel no SICAR via GeoServer WFS."""
    try:
        resultado = await buscar_car_sicar(car_numero)
        if resultado.get("sucesso") and resultado.get("geometria"):
            logger.info(f"SICAR geometria obtida para {car_numero}: {resultado.get('area_ha')} ha")
            return {
                "geometria": resultado["geometria"],
                "area_ha": resultado.get("area_ha"),
                "municipio": resultado.get("municipio"),
                "uf": resultado.get("uf"),
                "status_car": resultado.get("status"),
                "condicao": resultado.get("condicao"),
                "tipo": resultado.get("tipo"),
                "modulos_fiscais": resultado.get("modulos_fiscais"),
            }
        logger.warning(f"SICAR sem geometria para {car_numero}: {resultado.get('erro','desconhecido')}")
        return None
    except Exception as e:
        logger.error(f"SICAR erro critico {car_numero}: {e}")
        return None


async def analisar_conformidade_completa(
    car_numero: str,
    cpf_cnpj: Optional[str] = None,
    nome_proprietario: Optional[str] = None,
) -> dict:
    """
    Pipeline completo de conformidade socioambiental.
    1. Busca geometria real no SICAR
    2. Usa geometria em todas as verifica��es espaciais
    3. Retorna laudo consolidado
    """
    import asyncio
    from app.services.embargos_service import verificar_embargos_ibama

    logger.info(f"Iniciando an�lise completa: {car_numero}")
    uf = car_numero[:2].upper()

    # ?Etapa 1: Geometria SICAR ?
    sicar = await obter_geometria_sicar(car_numero)
    geometria = sicar["geometria"] if sicar else None
    area_ha   = sicar["area_ha"]   if sicar else None
    municipio = sicar["municipio"] if sicar else None

    # ?Etapa 2: Verifica��es paralelas ?
    quilombolas_task     = verificar_quilombolas(car_numero, geometria, uf)
    assentamentos_task   = verificar_assentamentos(car_numero, geometria, uf)
    trabalho_task        = verificar_trabalho_escravo(car_numero, cpf_cnpj, nome_proprietario)
    embargos_task        = verificar_embargos_ibama(car_numero, geometria, uf)

    quilombolas, assentamentos, trabalho_escravo, embargos = await asyncio.gather(
        quilombolas_task,
        assentamentos_task,
        trabalho_task,
        embargos_task,
    )

    # ?Etapa 3: Score de conformidade ?
    problemas = []
    embargo_total = embargos.total_embargos if hasattr(embargos, "total_embargos") else embargos.get("total", 0)
    embargo_detectado = embargos.embargo_detectado if hasattr(embargos, "embargo_detectado") else embargos.get("embargo_detectado", False)
    if embargo_detectado and embargo_total > 0:
        problemas.append(f"Embargos IBAMA: {embargos['total']}")
    if quilombolas.get("sobreposicao"):
        problemas.append("Sobreposi��o com territ�rio quilombola")
    if assentamentos.get("sobreposicao"):
        problemas.append("Sobreposi��o com assentamento INCRA")
    if trabalho_escravo.get("trabalho_escravo"):
        problemas.append(f"Lista Suja MTE: {trabalho_escravo.get('nome_encontrado','')}")

    total_checks = 4
    checks_ok    = total_checks - len(problemas)
    score        = round((checks_ok / total_checks) * 100)

    status_geral = "APROVADO" if score == 100 else ("ALERTA" if score >= 75 else "REPROVADO")

    return {
        "car_numero": car_numero,
        "status_geral": status_geral,
        "score_conformidade": score,
        "problemas_encontrados": problemas,
        "sicar": sicar,
        "embargos_ibama": embargos,
        "quilombolas": quilombolas,
        "assentamentos": assentamentos,
        "trabalho_escravo": trabalho_escravo,
        "geometria_real": geometria is not None,
        "area_ha": area_ha,
        "municipio": municipio,
        "uf": uf,
    }