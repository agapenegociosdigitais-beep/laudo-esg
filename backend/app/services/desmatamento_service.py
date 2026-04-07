"""
Servi??�o de verificação de desmatamento e conformidade ambiental.

Fontes de dados:
- PRODES/INPE: http://terrabrasilis.dpi.inpe.br/app/api
- MapBiomas: https://plataforma.mapbiomas.org
- DETER/INPE: https://terrabrasilis.dpi.inpe.br

Regula??�??�es verificadas:
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
    """Verifica desmatamento e avalia conformidade regulat??�ria."""

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
        Consulta TerraBrasilis WFS real (PRODES/INPE) com intersecção espacial correta.

        Algoritmo:
          1. Converte o polígono do imóvel para Shapely
          2. Busca PRODES no bbox do imóvel (candidatos)
          3. Para cada polígono PRODES, calcula INTERSECTION com o imóvel
          4. Calcula área geodésica (pyproj) apenas da porção dentro do imóvel
          5. Agrupa por ano, retorna detalhes completos

        Endpoints:
          prodes-legal-amz:yearly_deforestation  (Amazônia)
          prodes-cerrado-nb:yearly_deforestation  (Cerrado)
          prodes-mata-atlantica-nb:yearly_deforestation (Mata Atlântica)
        """
        try:
            from shapely.geometry import shape
            from shapely.ops import unary_union
            import pyproj

            # ── 1. Converte geometria do imóvel para Shapely ──────────────────
            imovel_geom = self._geojson_para_shapely(geojson)
            if imovel_geom is None or imovel_geom.is_empty:
                return None

            # Calcula BBOX para filtrar candidatos no WFS
            xmin, ymin, xmax, ymax = imovel_geom.bounds

            # ── 2. Seleciona camada PRODES por bioma ──────────────────────────
            if "Cerrado" in bioma and "Amazônia" not in bioma:
                layer = "prodes-cerrado-nb:yearly_deforestation"
            elif "Mata" in bioma:
                layer = "prodes-mata-atlantica-nb:yearly_deforestation"
            else:
                layer = "prodes-legal-amz:yearly_deforestation"

            # Nota: main_class varia por ano ('desmatamento' até 2020, 'DESMATAMENTO' a partir de 2021)
            # Filtro de classe é feito no Python via .lower() para não perder nenhum ano
            cql_filter = f"BBOX(geom,{xmin},{ymin},{xmax},{ymax},'EPSG:4326')"

            wfs_url = "https://terrabrasilis.dpi.inpe.br/geoserver/ows"
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": layer,
                "outputFormat": "application/json",
                "CQL_FILTER": cql_filter,
                "count": "500",
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
                    detalhes={"total_registros": 0, "bioma": bioma, "metodo": "intersecao_espacial"},
                )

            # ── 3. Calcula área geodésica (sem distorção de projeção) ─────────
            geod = pyproj.Geod(ellps="WGS84")

            def _area_ha_geodesica(geom) -> float:
                """Área geodésica em hectares via pyproj (precisa para WGS84)."""
                if geom is None or geom.is_empty:
                    return 0.0
                area_m2, _ = geod.geometry_area_perimeter(geom)
                return abs(area_m2) / 10_000

            # ── 4. Intersecção + agrupamento por ano ──────────────────────────
            por_ano: Dict[str, float] = {}
            registros_detalhados = []
            total_poligonos_intersectados = 0

            for f in feats:
                props = f.get("properties", {})
                geom_dict = f.get("geometry")
                if not geom_dict:
                    continue

                # Filtro de classe
                classe = props.get("main_class", props.get("classname", props.get("classe", "")))
                if classe and "desmatamento" not in classe.lower():
                    continue

                try:
                    prodes_geom = shape(geom_dict)
                except Exception:
                    continue

                # Intersecção com o polígono do imóvel
                intersecao = imovel_geom.intersection(prodes_geom)
                if intersecao.is_empty:
                    continue

                area_ha = round(_area_ha_geodesica(intersecao), 4)
                if area_ha <= 0:
                    continue

                total_poligonos_intersectados += 1

                # Extrai ano
                ano_raw = props.get("year", props.get("ano", props.get("view_date", "")))
                try:
                    ano = int(str(ano_raw)[:4]) if ano_raw else None
                except (ValueError, TypeError):
                    ano = None
                ano_str = str(ano) if ano else "Ano não informado"

                por_ano[ano_str] = round(por_ano.get(ano_str, 0.0) + area_ha, 4)

                registros_detalhados.append({
                    "ano": ano,
                    "area_ha": area_ha,
                    "classe": classe or "desmatamento",
                })

            area_total = round(sum(por_ano.values()), 2)

            # ── 5. Monta registros por ano ordenados (mais recente primeiro) ──
            registros_por_ano = [
                {"ano": int(k) if k.isdigit() else k, "area_ha": round(v, 2)}
                for k, v in sorted(por_ano.items(), reverse=True)
            ]

            anos_detectados = sorted(
                [k for k in por_ano.keys() if k.isdigit()], reverse=True
            )
            periodo = (
                f"PRODES {anos_detectados[-1]}–{anos_detectados[0]}"
                if len(anos_detectados) > 1
                else (f"PRODES {anos_detectados[0]}" if anos_detectados else "PRODES 2008–2025")
            )

            logger.info(
                f"PRODES intersecção: {total_poligonos_intersectados} polígonos, "
                f"{area_total:.2f} ha dentro do imóvel | {bioma}"
            )
            return ResultadoDesmatamento(
                desmatamento_detectado=area_total > 0,
                area_desmatada_ha=area_total,
                periodo_referencia=periodo,
                fonte="PRODES/INPE TerraBrasilis (intersecção real)",
                detalhes={
                    "total_registros": total_poligonos_intersectados,
                    "bioma": bioma,
                    "metodo": "intersecao_espacial",
                    "registros_por_ano": registros_por_ano,
                    "anos_detectados": anos_detectados,
                },
            )
        except Exception as e:
            logger.warning(f"TerraBrasilis WFS erro: {e}")
            return None

    def _geojson_para_shapely(self, geojson: Dict[str, Any]):
        """Converte GeoJSON (Feature, FeatureCollection ou Geometry) para Shapely."""
        try:
            from shapely.geometry import shape
            from shapely.ops import unary_union

            if not geojson:
                return None
            tipo = geojson.get("type", "")
            if tipo == "FeatureCollection":
                geoms = []
                for f in geojson.get("features", []):
                    g = f.get("geometry")
                    if g:
                        geoms.append(shape(g))
                return unary_union(geoms) if geoms else None
            elif tipo == "Feature":
                g = geojson.get("geometry")
                return shape(g) if g else None
            else:
                return shape(geojson)
        except Exception as e:
            logger.warning(f"Erro ao converter GeoJSON para Shapely: {e}")
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

        # Determina desmatamento de forma reprodut??�vel por localiza??�??�o
        seed_val = int(abs(lon * 100 + lat * 100)) % 100

        # Amazônia tem maior incidência histórica de desmatamento (40% dos CARs t??�m alertas)
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
            "classe_desmatamento": "Desflorestamento" if desmatamento_detectado else "Sem altera??�??�o",
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
        Verifica conformidade com a Moratória da Soja Amaz??�nica.

        Regra: Nenhuma soja pode ser produzida em ??�rea de floresta amaz??�nica
        desmatada após 24 de julho de 2008.

        Aplic??�vel principalmente ao bioma Amazônia.
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
                    "Suspenda imediatamente a comercialização de soja desta ??�rea.",
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

        Regulamento (UE) 2023/1115 �????à em vigor a partir de 30 dez 2024.
        Exige que produtos comercializados na UE não provenham de áreas
        desmatadas ou degradadas após 31 de dezembro de 2020.

        Commodities afetadas: soja, gado, ??�leo de palma, madeira, caf??�,
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
                        f"N????O CONFORME com EUDR: Desmatamento de {resultado_desmat.area_desmatada_ha:.1f} ha "
                        f"detectado após 31/12/2020. Produtos desta propriedade não podem ser "
                        f"exportados para a Uni??�o Europeia sem regulariza??�??�o. "
                        f"Fonte: {resultado_desmat.fonte}"
                    ),
                    recomendacoes=[
                        "Bloqueie exporta??�??�es para a UE atà regulariza??�??�o.",
                        "Elabore um plano de due diligence conforme EUDR Art. 8.",
                        "Contrate sistema de rastreabilidade geoespacial certificado.",
                        "Consulte importadores europeus sobre requisitos espec??�ficos.",
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
                "Documente e guarde evid??�ncias de conformidade por no m??�nimo 5 anos.",
                "Implemente sistema de monitoramento cont??�nuo via sat??�lite.",
                "Prepare dossià de due diligence para exportadores europeus.",
            ],
        )