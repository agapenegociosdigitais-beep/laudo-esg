"""
Serviço de verificação de desmatamento e conformidade ambiental.

Fontes de dados:
- PRODES/INPE: http://terrabrasilis.dpi.inpe.br/app/api
- MapBiomas: https://plataforma.mapbiomas.org
- DETER/INPE: https://terrabrasilis.dpi.inpe.br

Regulaççes verificadas:
1. Moratória da Soja (MSM): proíbe soja em áreas desmatadas após jul/2008
2. EUDR (EU Deforestation Regulation): ausência de desmatamento após dez/2020
"""
import logging
from datetime import date
from typing import Any, Dict

import httpx

from app.core.config import get_settings
from app.schemas.analise import ResultadoConformidade, ResultadoDesmatamento

logger = logging.getLogger(__name__)
settings = get_settings()

# Data de corte da Moratória da Soja: julho de 2008
DATA_CORTE_MORATORIO_SOJA = date(2008, 7, 24)

# Data de corte da EUDR: 31 de dezembro de 2020
DATA_CORTE_EUDR = date(2020, 12, 31)

# Biomas cobertos pela Moratória da Soja (aplicável à Amazônia)
BIOMAS_MORATORIO_SOJA = {"Amazônia", "Amazônia/Cerrado"}


class DesmatamentoService:
    """Verifica desmatamento e avalia conformidade regulatçria."""

    def __init__(self) -> None:
        self._cliente = httpx.AsyncClient(timeout=30)

    async def verificar_desmatamento(
        self,
        geojson: Dict[str, Any],
        bioma: str,
    ) -> ResultadoDesmatamento:
        """
        Verifica se hà desmatamento detectado na propriedade via PRODES/INPE.

        Args:
            geojson: GeoJSON da propriedade
            bioma: Bioma da propriedade (para contexto)

        Returns:
            ResultadoDesmatamento com detalhes do desmatamento detectado.
        """
        # Tenta API do TerraBrasilis (PRODES/INPE)
        # Consulta TerraBrasilis WFS real (PRODES/INPE)
        resultado = await self._consultar_terrabrasilis(geojson, bioma)
        if resultado:
            return resultado
        # Fallback simulacao se TerraBrasilis indisponivel
        logger.warning("TerraBrasilis indisponivel - usando simulacao")
        return self._simular_desmatamento(geojson, bioma)

    async def _consultar_terrabrasilis(
        self,
        geojson: Dict[str, Any],
        bioma: str,
    ) -> ResultadoDesmatamento | None:
        """
        Consulta TerraBrasilis WFS real (PRODES/INPE).
        Endpoint: https://terrabrasilis.dpi.inpe.br/geoserver/ows
        Camadas: prodes-legal-amz:yearly_deforestation (Amazonia)
                 prodes-cerrado-nb:yearly_deforestation (Cerrado)
        """
        try:
            # Extrai bbox da geometria
            coords = []
            def _ext(obj):
                if isinstance(obj, list):
                    if obj and isinstance(obj[0], (int, float)): coords.append(obj[:2])
                    else:
                        for i in obj: _ext(i)
                elif isinstance(obj, dict):
                    _ext(obj.get("coordinates") or obj.get("geometry") or [])
                    for f in obj.get("features", []): _ext(f)
            _ext(geojson)
            if not coords: return None
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            bbox = f"{min(xs)},{min(ys)},{max(xs)},{max(ys)},EPSG:4326"

            # Seleciona camada por bioma
            if "Cerrado" in bioma and "Amazonia" not in bioma and "Amaz?nia" not in bioma:
                layer = "prodes-cerrado-nb:yearly_deforestation"
                workspace = "prodes-cerrado-nb"
            elif "Mata" in bioma:
                layer = "prodes-mata-atlantica-nb:yearly_deforestation"
                workspace = "prodes-mata-atlantica-nb"
            else:
                layer = "prodes-legal-amz:yearly_deforestation"
                workspace = "prodes-legal-amz"

            wfs_url = "https://terrabrasilis.dpi.inpe.br/geoserver/ows"
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": layer,
                "outputFormat": "application/json",
                "bbox": bbox,
                "srsName": "EPSG:4326",
                "count": "50",
            }
            headers = {"User-Agent": "EurekaTerra/1.0 (compliance@eurekaterra.com)"}
            resp = await self._cliente.get(wfs_url, params=params, headers=headers, timeout=25)
            if resp.status_code != 200:
                logger.warning(f"TerraBrasilis WFS status {resp.status_code}")
                return None

            data = resp.json()
            feats = data.get("features", [])
            if not feats:
                return ResultadoDesmatamento(
                    desmatamento_detectado=False,
                    area_desmatada_ha=0.0,
                    periodo_referencia="2008-2025 (PRODES)",
                    fonte="PRODES/INPE TerraBrasilis",
                    detalhes={"total_registros": 0, "bioma": bioma},
                )

            area_total = 0.0
            anos = []
            registros = []
            for f in feats:
                props = f.get("properties", {})
                area = float(props.get("areakm", props.get("area_km", props.get("area", 0))) or 0)
                area_ha = round(area * 100, 4)  # km2 para ha
                ano = props.get("year", props.get("ano", props.get("view_date", "")))
                area_total += area_ha
                if ano: anos.append(str(ano))
                registros.append({"area_ha": area_ha, "ano": ano, "classe": props.get("classname", props.get("classe", ""))})

            logger.info(f"PRODES: {len(feats)} registros, {area_total:.2f} ha para {bioma}")
            return ResultadoDesmatamento(
                desmatamento_detectado=area_total > 0,
                area_desmatada_ha=round(area_total, 2),
                periodo_referencia=f"2008-2025 (PRODES anos: {chr(44).join(set(anos))})" if anos else "2008-2025 (PRODES)",
                fonte="PRODES/INPE TerraBrasilis (real)",
                detalhes={"total_registros": len(feats), "bioma": bioma, "registros": registros[:5]},
            )
        except Exception as e:
            logger.warning(f"TerraBrasilis WFS erro: {e}")
            return None

    def _simular_desmatamento(
        self,
        geojson: Dict[str, Any],
        bioma: str,
    ) -> ResultadoDesmatamento:
        """
        Simula resultado de desmatamento para desenvolvimento.
        A probabilidade de detecção varia por bioma.
        """
        # Extrai coordenada central para determinismo
        lon, lat = -55.0, -12.0
        try:
            if geojson.get("type") == "FeatureCollection":
                features = geojson.get("features", [])
                if features:
                    coords = features[0]["geometry"]["coordinates"][0]
                    lon = sum(c[0] for c in coords) / len(coords)
                    lat = sum(c[1] for c in coords) / len(coords)
        except Exception:
            pass

        # Determina desmatamento de forma reprodutçvel por localizaçço
        seed_val = int(abs(lon * 100 + lat * 100)) % 100

        # Amazônia tem maior incidência histórica de desmatamento (40% dos CARs tçm alertas)
        if "Amazônia" in bioma:
            desmatamento_detectado = seed_val < 35
            area_ha = round((seed_val % 20) * 2.5, 2) if desmatamento_detectado else 0.0
        elif "Cerrado" in bioma:
            desmatamento_detectado = seed_val < 25
            area_ha = round((seed_val % 15) * 1.8, 2) if desmatamento_detectado else 0.0
        else:
            desmatamento_detectado = seed_val < 15
            area_ha = round((seed_val % 10) * 1.2, 2) if desmatamento_detectado else 0.0

        detalhes = {
            "fonte": "PRODES/INPE (simulado)",
            "bioma": bioma,
            "classe_desmatamento": "Desflorestamento" if desmatamento_detectado else "Sem alteraçço",
            "ano_deteccao": 2021 + (seed_val % 3) if desmatamento_detectado else None,
        }

        return ResultadoDesmatamento(
            desmatamento_detectado=desmatamento_detectado,
            area_desmatada_ha=area_ha,
            periodo_referencia="2008-2024 (PRODES simulado)",
            fonte="PRODES/INPE (simulado)",
            detalhes=detalhes,
        )

    def verificar_moratorio_soja(
        self,
        resultado_desmat: ResultadoDesmatamento,
        bioma: str,
    ) -> ResultadoConformidade:
        """
        Verifica conformidade com a Moratória da Soja Amazçnica.

        Regra: Nenhuma soja pode ser produzida em çrea de floresta amazçnica
        desmatada após 24 de julho de 2008.

        Aplicçvel principalmente ao bioma Amazônia.
        """
        # Fora da Amazônia: regulação não se aplica diretamente
        if not any(b in bioma for b in BIOMAS_MORATORIO_SOJA):
            return ResultadoConformidade(
                conforme=True,
                nivel_risco="BAIXO",
                detalhe=(
                    f"Moratória da Soja se aplica à Amazônia. Bioma desta propriedade: {bioma}. "
                    "Verificar regras específicas do bioma."
                ),
                recomendacoes=[
                    f"Para o bioma {bioma}, consulte o Código Florestal (Lei 12.651/2012).",
                    "Verifique conformidade com APP e Reserva Legal.",
                ],
            )

        # Na Amazônia: verifica desmatamento
        if resultado_desmat.desmatamento_detectado and resultado_desmat.area_desmatada_ha > 0:
            detalhe = (
                f"ALERTA: Detectado {resultado_desmat.area_desmatada_ha:.1f} ha de desmatamento. "
                f"A Moratória da Soja proíbe cultivo em áreas desmatadas após jul/2008 na Amazônia. "
                f"Fonte: {resultado_desmat.fonte}"
            )
            return ResultadoConformidade(
                conforme=False,
                nivel_risco="CRÍTICO" if resultado_desmat.area_desmatada_ha > 10 else "ALTO",
                detalhe=detalhe,
                recomendacoes=[
                    "Suspenda imediatamente a comercialização de soja desta çrea.",
                    "Contrate auditoria ambiental independente.",
                    "Regularize a situação junto ao SICAR e MAPA.",
                    "Consulte advogado especialista em direito ambiental.",
                ],
            )

        return ResultadoConformidade(
            conforme=True,
            nivel_risco="BAIXO",
            detalhe="Nenhum desmatamento detectado após a data de corte da Moratória da Soja (jul/2008).",
            recomendacoes=[
                "Mantenha o CAR sempre atualizado.",
                "Realize monitoramento anual para manutenção da conformidade.",
            ],
        )

    def verificar_eudr(
        self,
        resultado_desmat: ResultadoDesmatamento,
    ) -> ResultadoConformidade:
        """
        Verifica conformidade com a EUDR (EU Deforestation Regulation).

        Regulamento (UE) 2023/1115 - em vigor a partir de 30 dez 2024.
        Exige que produtos comercializados na UE não provenham de áreas
        desmatadas ou degradadas após 31 de dezembro de 2020.

        Commodities afetadas: soja, gado, çleo de palma, madeira, cafç,
        cacau, borracha e produtos derivados.
        """
        if resultado_desmat.desmatamento_detectado and resultado_desmat.area_desmatada_ha > 0:
            detalhes_dict = resultado_desmat.detalhes or {}
            ano_deteccao = detalhes_dict.get("ano_deteccao")

            # Verifica se o desmatamento ocorreu após a data de corte EUDR
            desmatamento_pos_2020 = (
                ano_deteccao is None or  # Sem data confirmada = risco
                (isinstance(ano_deteccao, int) and ano_deteccao >= 2021)
            )

            if desmatamento_pos_2020:
                return ResultadoConformidade(
                    conforme=False,
                    nivel_risco="CRÍTICO",
                    detalhe=(
                        f"NÃO CONFORME com EUDR: Desmatamento de {resultado_desmat.area_desmatada_ha:.1f} ha "
                        f"detectado após 31/12/2020. Produtos desta propriedade não podem ser "
                        f"exportados para a Uniço Europeia sem regularizaçço. "
                        f"Fonte: {resultado_desmat.fonte}"
                    ),
                    recomendacoes=[
                        "Bloqueie exportaççes para a UE atà regularizaçço.",
                        "Elabore um plano de due diligence conforme EUDR Art. 8.",
                        "Contrate sistema de rastreabilidade geoespacial certificado.",
                        "Consulte importadores europeus sobre requisitos especçficos.",
                    ],
                )

        return ResultadoConformidade(
            conforme=True,
            nivel_risco="BAIXO",
            detalhe=(
                "Nenhum desmatamento detectado após 31/12/2020. "
                "Propriedade em conformidade com os requisitos da EUDR."
            ),
            recomendacoes=[
                "Documente e guarde evidçncias de conformidade por no mçnimo 5 anos.",
                "Implemente sistema de monitoramento contçnuo via satçlite.",
                "Prepare dossià de due diligence para exportadores europeus.",
            ],
        )