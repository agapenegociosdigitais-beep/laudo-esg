"""
Serviço de integração com o SICAR (Sistema de Cadastro Ambiental Rural).

Fontes de dados:
- API pública do SICAR: https://consultapublica.car.gov.br/publico
- Fallback: dados simulados realistas para desenvolvimento

Formato do número CAR: UF-IBGE-IDENTIFICADOR
Exemplo: MT-5107248-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""
import logging
import re
from typing import Optional

import httpx

from app.core.config import get_settings
from app.schemas.propriedade import CARResultado

logger = logging.getLogger(__name__)
settings = get_settings()

# Mapeamento de estados para biomas predominantes (simplificado)
ESTADO_BIOMA: dict[str, str] = {
    "AC": "Amazônia", "AM": "Amazônia", "AP": "Amazônia",
    "PA": "Amazônia", "RO": "Amazônia", "RR": "Amazônia",
    "TO": "Cerrado", "MT": "Amazônia/Cerrado", "MA": "Amazônia/Cerrado",
    "GO": "Cerrado", "DF": "Cerrado", "MS": "Cerrado/Pantanal",
    "MG": "Cerrado/Mata AtlÃƒÂ¢ntica", "SP": "Mata AtlÃƒÂ¢ntica/Cerrado",
    "RJ": "Mata AtlÃƒÂ¢ntica", "ES": "Mata AtlÃƒÂ¢ntica",
    "PR": "Mata AtlÃƒÂ¢ntica", "SC": "Mata AtlÃƒÂ¢ntica",
    "RS": "Mata AtlÃƒÂ¢ntica/Pampa", "BA": "Cerrado/Caatinga",
    "PI": "Caatinga/Cerrado", "CE": "Caatinga", "RN": "Caatinga",
    "PB": "Caatinga", "PE": "Caatinga", "AL": "Mata AtlÃƒÂ¢ntica",
    "SE": "Mata AtlÃƒÂ¢ntica", "PA": "Amazônia",
}


class CARService:
    """Serviço para consulta e validação de números CAR no SICAR."""

    def __init__(self) -> None:
        self._cliente_http = httpx.AsyncClient(
            timeout=settings.SICAR_TIMEOUT_SEGUNDOS,
            headers={"User-Agent": "EurekaTerra/0.1 (analytics@eurekaterra.com.br)"},
        )

    async def buscar_por_car(self, numero_car: str) -> CARResultado:
        """
        Busca os dados de uma propriedade pelo número do CAR.

        Tenta a API do SICAR primeiro; em caso de falha ou ambiente de
        desenvolvimento, retorna dados simulados realistas.
        """
        # Normaliza o numero CAR - remove pontos, espacos, uppercase
        numero_car = numero_car.strip().upper().replace(".", "").replace(" ", "")
        # Valida e extrai o estado do número CAR
        estado = self._extrair_estado(numero_car)
        if not estado:
            return CARResultado(
                numero_car=numero_car,
                estado="XX",
                municipio="Desconhecido",
                encontrado=False,
                fonte="Erro de validação",
            )

        # Busca sempre no SICAR real (WFS publico - sem autenticacao)
        from app.services.sicar_service import buscar_car_sicar
        resultado_sicar = await buscar_car_sicar(numero_car)
        if resultado_sicar.get("sucesso") and resultado_sicar.get("geometria"):
            uf = resultado_sicar.get("uf", estado)
            bioma = ESTADO_BIOMA.get(uf, "Desconhecido")
            geojson = resultado_sicar["geometria"]
            return CARResultado(
                numero_car=numero_car,
                estado=uf,
                municipio=resultado_sicar.get("municipio", ""),
                nome_propriedade=resultado_sicar.get("tipo", "Imovel Rural"),
                area_ha=resultado_sicar.get("area_ha"),
                status_car=resultado_sicar.get("status") or "Não informado",
                bioma=bioma,
                geojson=geojson,
                fonte="SICAR/GeoServer (real)",
                encontrado=True,
            )

        # Fallback: dados simulados se SICAR nao responder
        logger.warning(f"SICAR sem dados para {numero_car} - usando simulacao")
        return self._gerar_dado_simulado(numero_car, estado)

    async def _buscar_sicar(self, numero_car: str, estado: str) -> Optional[CARResultado]:
        """
        Consulta a API pública do SICAR pelo número do CAR.
        Retorna None se a propriedade não for encontrada ou ocorrer erro.
        """
        try:
            url = f"{settings.SICAR_API_URL}/imoveis/index"
            params = {"numeroImovel": numero_car}
            resposta = await self._cliente_http.get(url, params=params)
            resposta.raise_for_status()

            dados = resposta.json()
            if not dados or not isinstance(dados, dict):
                return None

            return CARResultado(
                numero_car=numero_car,
                estado=estado,
                municipio=dados.get("nomeMunicipio", ""),
                nome_propriedade=dados.get("nomeImovel"),
                area_ha=dados.get("areaImovelHa"),
                status_car=dados.get("situacaoCAR", "ATIVO"),
                bioma=dados.get("bioma"),
                geojson=dados.get("geometry"),
                fonte="SICAR",
                encontrado=True,
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"SICAR retornou erro HTTP {e.response.status_code} para CAR {numero_car}")
            return None
        except Exception as e:
            logger.warning(f"Erro ao consultar SICAR para CAR {numero_car}: {e}")
            return None

    def _extrair_estado(self, numero_car: str) -> Optional[str]:
        """
        Extrai o cÃƒÂ³digo do estado (UF) do número CAR.
        Formato esperado: UF-IBGE-IDENTIFICADOR
        """
        partes = numero_car.split("-")
        if len(partes) < 2:
            return None
        estado = partes[0].upper()
        estados_validos = {
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
            "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
            "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
        }
        return estado if estado in estados_validos else None

    def _gerar_dado_simulado(self, numero_car: str, estado: str) -> CARResultado:
        """
        Gera dados simulados realistas para demonstração e desenvolvimento.
        Cria um polÃƒÂ­gono retangular simples centrado no estado correspondente.
        """
        # CentrÃƒÂ³ides aproximados dos estados brasileiros (longitude, latitude)
        centroides: dict[str, tuple[float, float]] = {
            "MT": (-56.0, -13.0), "PA": (-52.0, -4.0), "AM": (-64.0, -4.0),
            "GO": (-49.5, -15.5), "MG": (-44.5, -18.5), "BA": (-41.5, -12.5),
            "MS": (-54.5, -20.5), "TO": (-48.0, -10.0), "MA": (-44.5, -5.5),
            "PI": (-42.5, -7.5), "CE": (-39.5, -5.5), "SP": (-48.5, -22.0),
            "PR": (-51.5, -24.5), "RS": (-53.0, -30.0), "SC": (-50.5, -27.5),
            "RO": (-63.0, -11.0), "AC": (-70.5, -9.0), "RR": (-61.5, 2.0),
            "AP": (-51.5, 1.5), "RJ": (-43.0, -22.5), "ES": (-40.5, -19.5),
            "SE": (-37.5, -10.5), "AL": (-36.5, -9.5), "PE": (-37.5, -8.5),
            "PB": (-36.5, -7.5), "RN": (-36.5, -5.5), "DF": (-47.9, -15.8),
        }
        lon, lat = centroides.get(estado, (-50.0, -15.0))

        # Variação aleatÃƒÂ³ria determinÃƒÂ­stica baseada no número CAR
        # para gerar coordenadas diferentes por propriedade
        hash_val = sum(ord(c) for c in numero_car) % 100
        offset_lon = (hash_val % 10 - 5) * 0.1
        offset_lat = (hash_val // 10 - 5) * 0.1
        lon += offset_lon
        lat += offset_lat

        # ÃƒÂrea simulada: polÃƒÂ­gono ~500 ha (~0.05 graus)
        delta = 0.025
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"numero_car": numero_car},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [lon - delta, lat - delta],
                            [lon + delta, lat - delta],
                            [lon + delta, lat + delta],
                            [lon - delta, lat + delta],
                            [lon - delta, lat - delta],
                        ]],
                    },
                }
            ],
        }

        municipios_por_estado: dict[str, list[str]] = {
            "MT": ["Sorriso", "Lucas do Rio Verde", "Nova Mutum", "Sinop"],
            "PA": ["SantarÃƒÂ©m", "MarabÃƒÂ¡", "Altamira", "Paragominas"],
            "GO": ["Rio Verde", "JataÃƒÂ­", "Mineiros", "Cristalina"],
            "MG": ["UnaÃƒÂ­", "Paracatu", "Patos de Minas", "UberlÃƒÂ¢ndia"],
            "BA": ["LuÃƒÂ­s Eduardo Magalhães", "Barreiras", "São DesidÃƒÂ©rio"],
            "MS": ["Dourados", "Campo Grande", "Sete Quedas"],
            "MA": ["Balsas", "São Raimundo das Mangabeiras"],
            "TO": ["Pedro Afonso", "Formoso do Araguaia", "Campos Lindos"],
        }
        municipios = municipios_por_estado.get(estado, ["MunicÃƒÂ­pio Simulado"])
        municipio = municipios[hash_val % len(municipios)]

        bioma = ESTADO_BIOMA.get(estado, "Cerrado")

        return CARResultado(
            numero_car=numero_car,
            estado=estado,
            municipio=municipio,
            nome_propriedade=f"Fazenda Demo {numero_car[-6:]}",
            area_ha=round(450 + (hash_val * 5.5), 2),
            status_car="ATIVO",
            bioma=bioma,
            geojson=geojson,
            fonte="Simulado (desenvolvimento)",
            encontrado=True,
        )