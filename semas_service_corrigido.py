"""
Serviço de integração com o SEMAS-PA (Secretaria de Estado de Meio Ambiente e Sustentabilidade).

Fonte: GeoServer WFS público do SECAR-PA (sem autenticação).
Endpoint: https://car.semas.pa.gov.br/geoserver/wfs
Layer: secar-pa:imovel

Campo de status: ind_status_imovel (PE, AT, CA, SU, IN, RE)
Campo de condição: des_condicao ("Aguardando análise", "Regular", etc.)

Normalização do número CAR para SEMAS:
  - Entrada:  PA-1501451-110F.7A95.5010.49E2.82B1.1240.815E.CA81
  - SEMAS:    PA-1501451-110F7A95501049E282B11240815ECA81  (pontos removidos)
"""
import logging
import httpx

logger = logging.getLogger(__name__)

SEMAS_WFS = "https://car.semas.pa.gov.br/geoserver/wfs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Mesmos códigos do SICAR nacional
STATUS_MAP = {
    "AT": "Ativo",
    "PE": "Pendente",
    "CA": "Cancelado",
    "SU": "Suspenso",
    "IN": "Inscrito",
    "RE": "Retificado",
    "AN": "Pendente",
    "NA": "Inativo",
}


def _normalizar_car_semas(numero_car: str) -> str:
    """
    Normaliza o número CAR para o formato usado pelo SEMAS-PA.
    Remove os pontos do identificador UUID mantendo o prefixo UF-IBGE-.

    Exemplos:
      PA-1501451-110F.7A95.5010.49E2.82B1.1240.815E.CA81
      → PA-1501451-110F7A95501049E282B11240815ECA81
    """
    partes = numero_car.split("-", 2)
    if len(partes) < 3:
        return numero_car
    uf, ibge, identificador = partes
    identificador_limpo = identificador.replace(".", "").upper()
    return f"{uf}-{ibge}-{identificador_limpo}"


async def buscar_car_semas(car_numero: str) -> dict:
    """
    Busca dados e status real de um CAR no GeoServer do SEMAS-PA.
    Retorna dict com sucesso, status, condição, área e geometria.

    Só deve ser chamado para CARs do estado do PA.
    """
    uf = car_numero[:2].upper()
    if uf != "PA":
        return {"sucesso": False, "erro": "SEMAS-PA só atende CARs do Pará (PA)", "car": car_numero}

    car_semas = _normalizar_car_semas(car_numero)

    try:
        async with httpx.AsyncClient(
            timeout=20, verify=False, headers=HEADERS
        ) as client:
            resp = await client.get(SEMAS_WFS, params={
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "secar-pa:imovel",
                "CQL_FILTER": f"cod_imovel='{car_semas}'",
                "outputFormat": "application/json",
                "count": 1,
                "propertyName": (
                    "cod_imovel,ind_status_imovel,nom_imovel,"
                    "num_area_imovel,dat_criacao,dat_atualizacao,"
                    "flg_ativo,des_condicao,idt_situacao_oema,"
                    "num_modulo_fiscal,geo_area_imovel"
                ),
            })
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])

            if not features:
                logger.warning(f"SEMAS-PA: CAR {car_semas} não encontrado")
                return {"sucesso": False, "erro": "CAR não encontrado no SEMAS-PA", "car": car_numero}

            feature = features[0]
            props = feature.get("properties", {})
            geom = feature.get("geometry")

            status_cod = props.get("ind_status_imovel") or ""
            status_descritivo = STATUS_MAP.get(status_cod, status_cod or "Não informado")
            condicao = props.get("des_condicao") or ""

            resultado = {
                "sucesso": True,
                "car": car_numero,
                "car_semas": car_semas,
                "status_codigo": status_cod,
                "status": status_descritivo,
                "condicao": condicao,
                "nome_imovel": props.get("nom_imovel", ""),
                "area_ha": props.get("num_area_imovel"),
                "modulos_fiscais": props.get("num_modulo_fiscal"),
                "ativo": props.get("flg_ativo", True),
                "dat_criacao": str(props.get("dat_criacao") or ""),
                "dat_atualizacao": str(props.get("dat_atualizacao") or ""),
                "geometria": geom,
                "fonte": "SEMAS-PA/GeoServer",
                "uf": "PA",
            }

            logger.info(
                f"SEMAS-PA: CAR {car_numero} → status={status_descritivo} "
                f"({status_cod}) | {condicao} | {resultado['area_ha']} ha"
            )
            return resultado

    except httpx.TimeoutException:
        logger.error(f"SEMAS-PA timeout para {car_numero}")
        return {"sucesso": False, "erro": "Timeout SEMAS-PA", "car": car_numero}
    except Exception as e:
        logger.error(f"SEMAS-PA erro para {car_numero}: {e}")
        return {"sucesso": False, "erro": str(e), "car": car_numero}
