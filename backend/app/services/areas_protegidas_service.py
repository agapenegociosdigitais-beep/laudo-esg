"""
Servi�o de verifica��o de sobreposi��o com �reas protegidas.

Fontes consultadas:
- CNUC/MMA (Cadastro Nacional de Unidades de Conserva��o ?Minist�rio do Meio Ambiente)
  API: https://sistemas.mma.gov.br/cnuc/
- FUNAI (Funda��o Nacional dos Povos Ind�genas)
  API: https://geoserver.funai.gov.br/geoserver/Funai/wfs

Comportamento quando API indispon�vel:
  Retorna status "n�o verificado" em vez de erro, garantindo que a an�lise
  prossiga mesmo sem conectividade com os servidores federais.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Unidades de Conserva��o de prote��o integral (mais restritivas)
CATEGORIAS_PROTECAO_INTEGRAL = {
    "Esta��o Ecol�gica",
    "Reserva Biol�gica",
    "Parque Nacional",
    "Parque Estadual",
    "Monumento Natural",
    "Ref�gio de Vida Silvestre",
}

# Unidades de Conserva��o de uso sustent�vel (menos restritivas)
CATEGORIAS_USO_SUSTENTAVEL = {
    "�rea de Prote��o Ambiental",
    "�rea de Relevante Interesse Ecol�gico",
    "Floresta Nacional",
    "Floresta Estadual",
    "Reserva Extrativista",
    "Reserva de Fauna",
    "Reserva de Desenvolvimento Sustent�vel",
    "Reserva Particular do Patrim�nio Natural",
}


class ResultadoAreaProtegida:
    """
    Resultado da verifica��o de sobreposi��o com �rea protegida.
    Cobre tanto Unidades de Conserva��o (UC) quanto Terras Ind�genas (TI).
    """

    def __init__(
        self,
        sobreposicao_detectada: Optional[bool],
        tipo_verificacao: str,  # "UC" ou "TI"
        nome_area: Optional[str] = None,
        categoria: Optional[str] = None,
        percentual_sobreposicao: Optional[float] = None,
        area_sobreposicao_ha: Optional[float] = None,
        esfera: Optional[str] = None,  # "Federal", "Estadual", "Municipal"
        fonte: str = "API",
        verificado: bool = True,
        motivo_nao_verificado: Optional[str] = None,
    ) -> None:
        # None = n�o verificado (API indispon�vel)
        # False = sem sobreposi��o
        # True = sobreposi��o detectada
        self.sobreposicao_detectada = sobreposicao_detectada
        self.tipo_verificacao = tipo_verificacao
        self.nome_area = nome_area
        self.categoria = categoria
        self.percentual_sobreposicao = percentual_sobreposicao
        self.area_sobreposicao_ha = area_sobreposicao_ha
        self.esfera = esfera
        self.fonte = fonte
        self.verificado = verificado
        self.motivo_nao_verificado = motivo_nao_verificado

    def para_dict(self) -> Dict[str, Any]:
        """Serializa para dicion�rio (armazenado em JSONB no banco)."""
        return {
            "sobreposicao_detectada": self.sobreposicao_detectada,
            "tipo_verificacao": self.tipo_verificacao,
            "nome_area": self.nome_area,
            "categoria": self.categoria,
            "percentual_sobreposicao": self.percentual_sobreposicao,
            "area_sobreposicao_ha": self.area_sobreposicao_ha,
            "esfera": self.esfera,
            "fonte": self.fonte,
            "verificado": self.verificado,
            "motivo_nao_verificado": self.motivo_nao_verificado,
            "status_display": self._calcular_status_display(),
        }

    def _calcular_status_display(self) -> str:
        """Retorna texto de status para o card do frontend."""
        if not self.verificado or self.sobreposicao_detectada is None:
            return "N�o verificado"
        if self.sobreposicao_detectada:
            pct = f" ({self.percentual_sobreposicao:.1f}%)" if self.percentual_sobreposicao else ""
            return f"Sobreposi��o detectada{pct}"
        return "Sem sobreposi��o"


class AreasProtegidasService:
    """
    Verifica sobreposi��o de uma propriedade com Unidades de Conserva��o (UC)
    e Terras Ind�genas (TI).

    Fluxo de consulta:
    1. Tenta API oficial (CNUC/MMA para UC, FUNAI/GeoServer para TI)
    """

    # WFS do CNUC/MMA para Unidades de Conserva��o
    CNUC_WFS_URL = "https://sistemas.mma.gov.br/cnuc/wfs"

    # WFS da FUNAI para Terras Ind�genas
    FUNAI_WFS_URL = "https://geoserver.funai.gov.br/geoserver/Funai/wfs"

    def __init__(self) -> None:
        # Timeout maior pois WFS com geometria pode ser lento
        self._cliente = httpx.AsyncClient(timeout=20)

    async def verificar_sobreposicao_uc(
        self,
        numero_car: str,
        geojson: Dict[str, Any],
        area_ha: float,
    ) -> ResultadoAreaProtegida:
        # ── 1. Cache local ──────────────────────────────────────────────────────
        try:
            from app.services.cache_local_service import consultar_uc_local
            local = await consultar_uc_local(geojson)
            if local:
                r = local[0]
                pct = round((float(r.get("area_intersecao_ha") or 0) / area_ha * 100), 2) if area_ha > 0 else None
                return ResultadoAreaProtegida(
                    sobreposicao_detectada=True,
                    tipo_verificacao="UC",
                    nome_area=r.get("nome_uc"),
                    categoria=r.get("categoria"),
                    percentual_sobreposicao=pct,
                    area_sobreposicao_ha=float(r.get("area_intersecao_ha") or 0),
                    esfera=r.get("orgao"),
                    fonte="CNUC/MMA (cache local)",
                    verificado=True,
                )
            return ResultadoAreaProtegida(
                sobreposicao_detectada=False,
                tipo_verificacao="UC",
                fonte="CNUC/MMA (cache local)",
                verificado=True,
            )
        except Exception as e:
            logger.warning(f"Cache UC indisponivel: {e}")

        # ── 2. API ao vivo ──────────────────────────────────────────────────────
        resultado = await self._consultar_cnuc(geojson)
        if resultado is not None:
            return resultado

        return ResultadoAreaProtegida(
            sobreposicao_detectada=None,
            tipo_verificacao="UC",
            verificado=False,
            motivo_nao_verificado="CNUC/MMA indisponível (cache vazio + API offline)",
        )

    async def verificar_sobreposicao_ti(
        self,
        numero_car: str,
        geojson: Dict[str, Any],
        area_ha: float,
    ) -> ResultadoAreaProtegida:
        # ── 1. Cache local ──────────────────────────────────────────────────────
        try:
            from app.services.cache_local_service import consultar_ti_local
            local = await consultar_ti_local(geojson)
            if local:
                r = local[0]
                pct = round((float(r.get("area_intersecao_ha") or 0) / area_ha * 100), 2) if area_ha > 0 else None
                return ResultadoAreaProtegida(
                    sobreposicao_detectada=True,
                    tipo_verificacao="TI",
                    nome_area=r.get("nome_ti"),
                    categoria="Terra Indígena Homologada",
                    percentual_sobreposicao=pct,
                    area_sobreposicao_ha=float(r.get("area_intersecao_ha") or 0),
                    esfera="Federal",
                    fonte="FUNAI (cache local)",
                    verificado=True,
                )
            return ResultadoAreaProtegida(
                sobreposicao_detectada=False,
                tipo_verificacao="TI",
                fonte="FUNAI (cache local)",
                verificado=True,
            )
        except Exception as e:
            logger.warning(f"Cache TI indisponível: {e}")

        # ── 2. API ao vivo ──────────────────────────────────────────────────────
        resultado = await self._consultar_funai(geojson)
        if resultado is not None:
            return resultado

        return ResultadoAreaProtegida(
            sobreposicao_detectada=None,
            tipo_verificacao="TI",
            verificado=False,
            motivo_nao_verificado="FUNAI indisponível (cache vazio + API offline)",
        )

    # ?Consultas �s APIs reais (WFS) ?

    async def _consultar_cnuc(
        self, geojson: Dict[str, Any]
    ) -> Optional[ResultadoAreaProtegida]:
        """
        Consulta o WFS do CNUC/MMA para verificar sobreposi��o com UCs.

        Usa requisi��o WFS GetFeature com filtro de interse��o espacial (CQL).
        Retorna None se o servi�o estiver indispon�vel.
        """
        try:
            wkt = self._geojson_para_wkt(geojson)
            if not wkt:
                return None

            params = {
                "service": "WFS",
                "version": "1.1.0",
                "request": "GetFeature",
                "typeNames": "cnuc:unidades_conservacao",
                "outputFormat": "application/json",
                "CQL_FILTER": f"INTERSECTS(geom, {wkt})",
                "count": "1",
            }

            resposta = await self._cliente.get(
                self.CNUC_WFS_URL,
                params=params,
                headers={"Accept": "application/json"},
            )

            if resposta.status_code != 200:
                logger.warning(f"CNUC/MMA retornou HTTP {resposta.status_code}.")
                return None

            dados = resposta.json()
            features = dados.get("features", [])

            if not features:
                return ResultadoAreaProtegida(
                    sobreposicao_detectada=False,
                    tipo_verificacao="UC",
                    fonte="CNUC/MMA",
                    verificado=True,
                )

            # Captura dados da primeira UC sobreposta
            props = features[0].get("properties", {})
            return ResultadoAreaProtegida(
                sobreposicao_detectada=True,
                tipo_verificacao="UC",
                nome_area=props.get("nome_uc"),
                categoria=props.get("categoria"),
                percentual_sobreposicao=float(props.get("perc_sobreposicao", 0)),
                area_sobreposicao_ha=float(props.get("area_sobreposicao_ha", 0)),
                esfera=props.get("esfera_administrativa"),
                fonte="CNUC/MMA",
                verificado=True,
            )

        except httpx.TimeoutException:
            logger.warning("Timeout ao consultar WFS CNUC/MMA.")
            return None
        except Exception as e:
            logger.warning(f"Erro ao consultar CNUC/MMA: {e}")
            return None

    async def _consultar_funai(
        self, geojson: Dict[str, Any]
    ) -> Optional[ResultadoAreaProtegida]:
        """
        Consulta o GeoServer da FUNAI para verificar sobreposi��o com TIs.

        Usa requisi��o WFS GetFeature com filtro CQL de interse��o.
        Retorna None se o servi�o estiver indispon�vel.
        """
        try:
            wkt = self._geojson_para_wkt(geojson)
            if not wkt:
                return None

            params = {
                "service": "WFS",
                "version": "1.1.0",
                "request": "GetFeature",
                "typeNames": "Funai:tis_homologadas",
                "outputFormat": "application/json",
                "CQL_FILTER": f"INTERSECTS(geom, {wkt})",
                "count": "1",
            }

            resposta = await self._cliente.get(
                self.FUNAI_WFS_URL,
                params=params,
                headers={"Accept": "application/json"},
            )

            if resposta.status_code != 200:
                logger.warning(f"FUNAI GeoServer retornou HTTP {resposta.status_code}.")
                return None

            dados = resposta.json()
            features = dados.get("features", [])

            if not features:
                return ResultadoAreaProtegida(
                    sobreposicao_detectada=False,
                    tipo_verificacao="TI",
                    fonte="FUNAI/GeoServer",
                    verificado=True,
                )

            props = features[0].get("properties", {})
            return ResultadoAreaProtegida(
                sobreposicao_detectada=True,
                tipo_verificacao="TI",
                nome_area=props.get("terrai_nom"),
                categoria="Terra Ind�gena Homologada",
                percentual_sobreposicao=float(props.get("perc_sobreposicao", 0)),
                area_sobreposicao_ha=float(props.get("area_sobreposicao_ha", 0)),
                esfera="Federal",
                fonte="FUNAI/GeoServer",
                verificado=True,
            )

        except httpx.TimeoutException:
            logger.warning("Timeout ao consultar GeoServer FUNAI.")
            return None
        except Exception as e:
            logger.warning(f"Erro ao consultar FUNAI: {e}")
            return None


    
    
    def _extrair_latitude(self, geojson: Dict[str, Any]) -> float:
        """
        Extrai latitude central do GeoJSON para estimativa de bioma.
        Retorna -15.0 (centro do Brasil) como fallback.
        """
        try:
            if geojson.get("type") == "FeatureCollection":
                features = geojson.get("features", [])
                if features:
                    coords = features[0]["geometry"]["coordinates"][0]
                    return sum(c[1] for c in coords) / len(coords)
            elif geojson.get("type") == "Feature":
                coords = geojson["geometry"]["coordinates"][0]
                return sum(c[1] for c in coords) / len(coords)
        except Exception:
            pass
        return -15.0

    def _geojson_para_wkt(self, geojson: Dict[str, Any]) -> Optional[str]:
        """
        Converte GeoJSON para WKT (Well-Known Text) para uso em filtros WFS.

        Suporta Feature, FeatureCollection e Polygon/MultiPolygon diretamente.
        Retorna None se n�o for poss�vel extrair a geometria.
        """
        try:
            geometria = None

            if geojson.get("type") == "FeatureCollection":
                features = geojson.get("features", [])
                if features:
                    geometria = features[0].get("geometry")
            elif geojson.get("type") == "Feature":
                geometria = geojson.get("geometry")
            elif geojson.get("type") in ("Polygon", "MultiPolygon"):
                geometria = geojson

            if not geometria:
                return None

            tipo = geometria.get("type", "")
            coords = geometria.get("coordinates", [])

            if tipo == "Polygon":
                anel_externo = coords[0]
                pontos = ", ".join(f"{lon} {lat}" for lon, lat in anel_externo)
                return f"POLYGON(({pontos}))"

            elif tipo == "MultiPolygon":
                # Usa apenas o primeiro pol�gono para simplificar o filtro WFS
                anel_externo = coords[0][0]
                pontos = ", ".join(f"{lon} {lat}" for lon, lat in anel_externo)
                return f"POLYGON(({pontos}))"

        except Exception as e:
            logger.warning(f"Erro ao converter GeoJSON para WKT: {e}")

        return None
