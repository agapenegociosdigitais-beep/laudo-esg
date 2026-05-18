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
    "MG": "Cerrado/Mata Atlântica", "SP": "Mata Atlântica/Cerrado",
    "RJ": "Mata Atlântica", "ES": "Mata Atlântica",
    "PR": "Mata Atlântica", "SC": "Mata Atlântica",
    "RS": "Mata Atlântica/Pampa", "BA": "Cerrado/Caatinga",
    "PI": "Caatinga/Cerrado", "CE": "Caatinga", "RN": "Caatinga",
    "PB": "Caatinga", "PE": "Caatinga", "AL": "Mata Atlântica",
    "SE": "Mata Atlântica", "PA": "Amazônia",
}


class CARService:
    """Serviço para consulta e validação de números CAR no SICAR."""

    def __init__(self) -> None:
        self._cliente_http = httpx.AsyncClient(
            timeout=settings.SICAR_TIMEOUT_SEGUNDOS,
            headers={"User-Agent": "EurekaTerra/0.1 (analytics@eurekaterra.com.br)"},
        )

    async def buscar_por_car(self, numero_car: str) -> CARResultado:
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

        # ── 0. Cache local (PostGIS) ──────────────────────────────────────
        try:
            from app.services.cache_local_service import consultar_car_local
            local = await consultar_car_local(numero_car)
            if local:
                r = local[0]
                return CARResultado(
                    numero_car=numero_car,
                    estado=r.get("estado", estado),
                    municipio=r.get("municipio", ""),
                    nome_propriedade=r.get("nome_imovel", "Imovel Rural"),
                    area_ha=float(r.get("area_ha") or 0),
                    status_car=r.get("status", "Ativo"),
                    bioma=ESTADO_BIOMA.get(estado, "Desconhecido"),
                    geojson=r.get("geometria_json"),
                    fonte="GeoServer Nacional (cache local)",
                    encontrado=True,
                )
        except Exception as e:
            logger.warning(f"Cache local indisponivel: {e}")

        # ── 0.5 GeoServer nacional (consulta direta, sem download) ───────
        try:
            from app.services.cache_local_service import consultar_car_geoserver
            gs = await consultar_car_geoserver(numero_car)
            if gs:
                return CARResultado(
                    numero_car=numero_car,
                    estado=gs.get("estado", estado),
                    municipio=gs.get("municipio", ""),
                    nome_propriedade=gs.get("nome_imovel", "Imovel Rural"),
                    area_ha=float(gs.get("area_ha") or 0),
                    status_car=gs.get("status", "Pendente"),
                    bioma=ESTADO_BIOMA.get(estado, "Desconhecido"),
                    geojson=gs.get("geometria"),
                    fonte="GeoServer Nacional (consulta direta)",
                    encontrado=True,
                )
        except Exception as e:
            logger.warning(f"GeoServer nacional indisponivel: {e}")

        # ── Etapa 1: SEMAS-PA (prioritário para CARs do Pará) ───────────────────
        if estado == "PA":
            from app.services.semas_service import buscar_car_semas
            resultado_semas = await buscar_car_semas(numero_car)
            if resultado_semas.get("sucesso"):
                bioma = ESTADO_BIOMA.get("PA", "Amazônia")
                geojson = resultado_semas.get("geometria")
                status = resultado_semas.get("status") or "Não informado"
                condicao = resultado_semas.get("condicao") or ""
                nome = resultado_semas.get("nome_imovel") or "Imóvel Rural"
                fonte_txt = f"SEMAS-PA/GeoServer (real)"
                if condicao:
                    fonte_txt += f" — {condicao}"

                # SEMAS não retorna nome do município — busca no SICAR nacional
                municipio = ""
                try:
                    from app.services.sicar_service import buscar_car_sicar
                    sicar = await buscar_car_sicar(numero_car)
                    if sicar.get("sucesso"):
                        municipio = sicar.get("municipio") or ""
                except Exception:
                    pass

                return CARResultado(
                    numero_car=numero_car,
                    estado="PA",
                    municipio=municipio,
                    nome_propriedade=nome,
                    area_ha=resultado_semas.get("area_ha"),
                    status_car=status,
                    bioma=bioma,
                    geojson=geojson,
                    fonte=fonte_txt,
                    encontrado=True,
                )
            logger.warning(f"SEMAS-PA sem dados para {numero_car}, tentando SICAR nacional")

        # ── Etapa 2: SICAR nacional (WFS público) ────────────────────────────────
        from app.services.sicar_service import buscar_car_sicar
        resultado_sicar = await buscar_car_sicar(numero_car)

        # Usa dados reais do SICAR se encontrado — mesmo sem geometria (CARs Pendentes/Suspensos
        # frequentemente nao possuem geometria no WFS mas têm status real)
        if resultado_sicar.get("sucesso"):
            uf = resultado_sicar.get("uf", estado)
            bioma = ESTADO_BIOMA.get(uf, "Desconhecido")
            geojson = resultado_sicar.get("geometria")  # pode ser None para CARs não ativos
            status = resultado_sicar.get("status") or "Não informado"
            return CARResultado(
                numero_car=numero_car,
                estado=uf,
                municipio=resultado_sicar.get("municipio", ""),
                nome_propriedade=resultado_sicar.get("tipo", "Imovel Rural"),
                area_ha=resultado_sicar.get("area_ha"),
                status_car=status,
                bioma=bioma,
                geojson=geojson,
                fonte="SICAR/GeoServer (real)",
                encontrado=True,
            )

        # ── Nao encontrado em nenhuma fonte ──────────────────────────────────
        logger.warning(f"CAR nao encontrado em nenhuma fonte (cache + SEMAS-PA + SICAR): {numero_car}")
        return CARResultado(
            numero_car=numero_car,
            estado=estado,
            municipio="Nao encontrado",
            encontrado=False,
            fonte="Nenhuma fonte disponivel (cache + APIs externas offline)",
        )

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
        Extrai o código do estado (UF) do número CAR.
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

