import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.core.config import get_settings
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
settings = get_settings()

VERDE_ESCURO  = HexColor("#0d3b1e")
VERDE         = HexColor("#1b5e20")
VERDE_MEDIO   = HexColor("#2e7d32")
VERDE_CLARO   = HexColor("#e8f5e9")
DOURADO       = HexColor("#f9a825")
VERMELHO      = HexColor("#b71c1c")
VERMELHO_CLARO= HexColor("#ffebee")
LARANJA       = HexColor("#e65100")
CINZA_ESCURO  = HexColor("#212121")
CINZA         = HexColor("#757575")
CINZA_CLARO   = HexColor("#f5f5f5")
CINZA_BORDA   = HexColor("#e0e0e0")
AZUL_INFO     = HexColor("#1565c0")
AZUL_CLARO    = HexColor("#e3f2fd")
BRANCO        = white


class RelatorioService:

    def __init__(self):
        os.makedirs(settings.REPORTS_DIR, exist_ok=True)

    @staticmethod
    def _clean(txt):
        if not txt:
            return ""
        return str(txt).replace('\u2013', '-').replace('\u2014', '-')

    @staticmethod
    def _cor_risco(risco):
        return {
            "BAIXO": (VERDE, VERDE_CLARO),
            "MEDIO": (LARANJA, HexColor("#fff3e0")),
            "ALTO": (VERMELHO, VERMELHO_CLARO),
            "CRITICO": (VERMELHO, VERMELHO_CLARO),
        }.get((risco or "ALTO").upper(), (VERMELHO, VERMELHO_CLARO))

    def _secao_header(self, numero, titulo):
        return Table(
            [[
                Paragraph(f"<b>{numero}</b>", ParagraphStyle("sn", fontSize=12, textColor=white, alignment=TA_CENTER, fontName="Helvetica-Bold")),
                Paragraph(f"<b>{titulo.upper()}</b>", ParagraphStyle("st", fontSize=10, textColor=white, fontName="Helvetica-Bold")),
            ]],
            colWidths=[1.2*cm, 15.8*cm],
            style=TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), VERDE_MEDIO),
                ("TOPPADDING", (0,0), (-1,-1), 8),
                ("BOTTOMPADDING", (0,0), (-1,-1), 8),
                ("LEFTPADDING", (0,0), (0,0), 6),
                ("LEFTPADDING", (1,0), (1,0), 12),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        )

    def _gerar_mapa(self, propriedade: Propriedade):
        try:
            from staticmap import StaticMap, Line
            from shapely.geometry import shape as shapely_shape
            import sqlalchemy as sa
        except ImportError:
            return None

        geojson = propriedade.geojson
        if not geojson:
            return None

        try:
            geom = shapely_shape(geojson)
            lon_min, lat_min, lon_max, lat_max = geom.bounds
        except Exception:
            return None

        pad = max((lon_max - lon_min), (lat_max - lat_min)) * 0.25 or 0.01
        lon_min -= pad; lat_min -= pad; lon_max += pad; lat_max += pad

        W, H = 800, 420
        mapa = StaticMap(W, H, url_template="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")

        coords = list(geom.exterior.coords) if geom.geom_type == "Polygon" else []
        if not coords and hasattr(geom, "geoms"):
            for g in geom.geoms:
                coords.extend(list(g.exterior.coords))
        if coords:
            mapa.add_line(Line([(c[0], c[1]) for c in coords], "#00e600", 3))

        try:
            db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2://", "postgresql://")
            engine_sync = sa.create_engine(db_url)
            import json as _json
            geo_str = _json.dumps(geojson)
            with engine_sync.connect() as conn:
                rows = conn.execute(
                    sa.text("""
                        SELECT year, ST_AsGeoJSON(ST_Intersection(geom, ST_GeomFromGeoJSON(:geo))) AS geom_json
                        FROM cache_prodes
                        WHERE ST_Intersects(geom, ST_GeomFromGeoJSON(:geo))
                        LIMIT 20
                    """),
                    {"geo": geo_str},
                ).fetchall()

                for row in rows:
                    year = row[0]
                    gjson = _json.loads(row[1]) if row[1] else None
                    if not gjson:
                        continue
                    if int(year) >= 2021:
                        cor_p, cor_c = "#ff0000", "#990000"
                    elif int(year) >= 2017:
                        cor_p, cor_c = "#ff6600", "#993300"
                    else:
                        cor_p, cor_c = "#ffaa00", "#996600"

                    try:
                        pgeom = shapely_shape(gjson)
                        polys = [pgeom] if pgeom.geom_type == "Polygon" else list(pgeom.geoms)
                        for poly in polys:
                            pts = [(c[0], c[1]) for c in poly.exterior.coords]
                            for offset in [0.00002, 0.00004]:
                                shifted = [(x + offset, y + offset) for x, y in pts]
                                mapa.add_line(Line(shifted, cor_p, 16))
                            mapa.add_line(Line(pts, cor_c, 2))
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"PRODES mapa: {e}")

        img_io = BytesIO()
        try:
            image = mapa.render()
            image.save(img_io, format="PNG", optimize=True)
            img_io.seek(0)
            return img_io
        except Exception:
            return None

    async def gerar_pdf(self, analise: Analise, propriedade: Propriedade, usuario: Usuario):
        car_safe = propriedade.numero_car.replace("/", "-")[:30]
        id_laudo = uuid.uuid4().hex[:8].upper()
        nome_arquivo = f"relatorio_{car_safe}_{id_laudo.lower()}.pdf"
        caminho_pdf = Path(settings.REPORTS_DIR) / nome_arquivo

        buffer = BytesIO()
        W, H = A4
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
        score = analise.score_esg or 0
        risco = (analise.nivel_risco or "ALTO").upper()
        cor_risco, bg_risco = self._cor_risco(risco)

        def rodape(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(VERDE_ESCURO)
            canvas.rect(0, 0, W, 0.9*cm, fill=1, stroke=0)
            canvas.setFillColor(HexColor("#a5d6a7"))
            canvas.setFont("Helvetica", 6.5)
            canvas.drawString(1.8*cm, 0.28*cm, f"Eureka Terra | Laudo #{id_laudo} | CAR: {propriedade.numero_car}")
            canvas.drawRightString(W - 1.8*cm, 0.28*cm, f"Pag. {doc.page} | {data_geracao}")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=1.2*cm, bottomMargin=1.4*cm,
            title=f"Laudo ESG #{id_laudo}",
            author="Eureka Terra",
        )

        # Estilos
        h1 = ParagraphStyle("h1", fontSize=12, textColor=VERDE, fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=8)
        h2 = ParagraphStyle("h2", fontSize=10, textColor=VERDE_MEDIO, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=5)
        normal = ParagraphStyle("normal", fontSize=9, fontName="Helvetica", spaceAfter=3, leading=13, textColor=CINZA_ESCURO)
        small = ParagraphStyle("small", fontSize=7.5, fontName="Helvetica", textColor=CINZA, leading=11)
        small_center = ParagraphStyle("sc", fontSize=7.5, fontName="Helvetica", textColor=CINZA, alignment=TA_CENTER)
        bold = ParagraphStyle("bold", fontSize=9, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)
        capa_t = ParagraphStyle("ct", fontSize=26, textColor=white, fontName="Helvetica-Bold", alignment=TA_CENTER)
        capa_s = ParagraphStyle("cs", fontSize=10, textColor=HexColor("#a5d6a7"), fontName="Helvetica", alignment=TA_CENTER)
        capa_v = ParagraphStyle("cv", fontSize=12, textColor=DOURADO, fontName="Helvetica-Bold", alignment=TA_CENTER)
        capa_i = ParagraphStyle("capa_i", fontSize=9, textColor=HexColor("#c8e6c9"), fontName="Helvetica", alignment=TA_CENTER)
        capa_n = ParagraphStyle("capa_n", fontSize=10, textColor=DOURADO, fontName="Helvetica-Bold", alignment=TA_CENTER)
        capa_sl = ParagraphStyle("capa_sl", fontSize=9, textColor=HexColor("#81c784"), fontName="Helvetica", alignment=TA_CENTER)
        rodape_s = ParagraphStyle("rodape_s", fontSize=8, textColor=HexColor("#81c784"), fontName="Helvetica", alignment=TA_CENTER)
        score_n = ParagraphStyle("scn", fontSize=44, fontName="Helvetica-Bold", alignment=TA_CENTER)
        risco_l = ParagraphStyle("rl", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)
        aviso = ParagraphStyle("av", fontSize=8, fontName="Helvetica", textColor=AZUL_INFO, leading=11, alignment=TA_JUSTIFY)
        th = ParagraphStyle("th", fontSize=8, fontName="Helvetica-Bold", textColor=white)
        th_c = ParagraphStyle("thc", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)
        td = ParagraphStyle("td", fontSize=8, fontName="Helvetica", textColor=CINZA_ESCURO, leading=11)
        td_b = ParagraphStyle("tdb", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)
        td_c = ParagraphStyle("tdc", fontSize=8, fontName="Helvetica", textColor=CINZA_ESCURO, alignment=TA_CENTER)
        td_s = ParagraphStyle("tds", fontSize=7.5, fontName="Helvetica", textColor=CINZA, leading=10)

        story = []

        # ═══════════ CAPA ═══════════
        capa = Table([
            [Paragraph("EUREKA TERRA", capa_t)],
            [Spacer(1, 6)],
            [Paragraph("Plataforma de Auditoria Ambiental ESG", capa_s)],
            [Spacer(1, 12)],
            [HRFlowable(width="40%", thickness=1, color=DOURADO, spaceAfter=0, spaceBefore=0)],
            [Spacer(1, 12)],
            [Paragraph("LAUDO DE CONFORMIDADE AMBIENTAL", capa_v)],
            [Paragraph("Propriedade Rural | Amazonia Legal", capa_sl)],
            [Spacer(1, 16)],
            [Paragraph(f"N. {id_laudo}", capa_n)],
            [Spacer(1, 12)],
            [Paragraph(f"CAR: {propriedade.numero_car}", capa_i)],
            [Paragraph(f"Imovel: {self._clean(propriedade.nome_propriedade) or 'Imovel Rural'}", capa_i)],
            [Paragraph(f"Municipio/UF: {self._clean(propriedade.municipio)} - {propriedade.estado}", capa_i)],
            [Paragraph(f"Area: {propriedade.area_ha or 0:.1f} ha | Bioma: {self._clean(propriedade.bioma) or 'Amazonia'}", capa_i)],
            [Spacer(1, 16)],
            [HRFlowable(width="40%", thickness=0.5, color=HexColor("#388e3c"), spaceAfter=0, spaceBefore=0)],
            [Spacer(1, 10)],
            [Paragraph(f"Emitido em {data_geracao} | Solicitante: {usuario.nome}", rodape_s)],
            [Paragraph("Validade: 90 dias | Uso restrito ao imovel analisado | Dados declaratorios", rodape_s)],
        ], colWidths=[17.4*cm])
        capa.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), VERDE_ESCURO),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("LEFTPADDING", (0,0), (-1,-1), 14),
            ("RIGHTPADDING", (0,0), (-1,-1), 14),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ]))
        story.append(capa)
        story.append(Spacer(1, 18))

        # ═══════════ SCORE ESG ═══════════
        story.append(self._secao_header("1", "Score ESG"))
        story.append(Spacer(1, 10))

        score_tbl = Table([
            [
                Paragraph(f'<font color="{cor_risco.hexval()}">{score:.0f}</font>', score_n),
                Paragraph(f'<font color="{cor_risco.hexval()}">{risco}</font>', risco_l),
            ],
            [
                Paragraph("Score ESG / 100", small_center),
                Paragraph("Nivel de Risco", small_center),
            ],
        ], colWidths=[8.7*cm, 8.7*cm])
        score_tbl.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 1.5, cor_risco),
            ("BACKGROUND", (0,0), (-1,-1), bg_risco),
            ("TOPPADDING", (0,0), (-1,-1), 16),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(score_tbl)
        story.append(Spacer(1, 10))

        # ═══════════ CONFORMIDADE ═══════════
        def _status(val):
            if val is True: return ("CONFORME", VERDE)
            if val is False: return ("NAO CONFORME", VERMELHO)
            return ("NAO VERIFICADO", CINZA)

        story.append(Paragraph("<b>Conformidade Regulatoria</b>", h2))

        itens = [
            ("Moratoria da Soja (jul/2008)", analise.moratorio_soja_conforme, self._clean(analise.moratorio_soja_detalhe) or "PRODES/INPE"),
            ("EUDR - Reg. UE 2023/1115 (2021-2025)", analise.eudr_conforme, self._clean(analise.eudr_detalhe) or "PRODES/INPE"),
        ]
        conf_rows = [[Paragraph("<b>Regulacao</b>", th), Paragraph("<b>Status</b>", th_c), Paragraph("<b>Detalhe</b>", th)]]
        for nome, val, det in itens:
            st, cor = _status(val)
            conf_rows.append([
                Paragraph(nome, td_b),
                Paragraph(f'<font color="{cor.hexval()}"><b>{st}</b></font>', ParagraphStyle("x", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(det[:120], td_s),
            ])
        story.append(Table(conf_rows, colWidths=[5.5*cm, 3.5*cm, 8.4*cm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE_MEDIO),
            ("GRID", (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [BRANCO, VERDE_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ])))
        story.append(Spacer(1, 14))

        # ═══════════ PROPRIEDADE ═══════════
        story.append(self._secao_header("2", "Identificacao da Propriedade"))
        story.append(Spacer(1, 8))

        prop_rows = [
            [Paragraph("<b>Campo</b>", th), Paragraph("<b>Valor</b>", th)],
            ["Numero CAR", propriedade.numero_car],
            ["Status CAR", self._clean(propriedade.status_car) or "ATIVO"],
            ["Nome do Imovel", self._clean(propriedade.nome_propriedade) or "Imovel Rural"],
            ["Municipio / UF", f"{self._clean(propriedade.municipio)} / {propriedade.estado}"],
            ["Bioma", self._clean(propriedade.bioma) or "Amazonia"],
            ["Area Declarada", f"{propriedade.area_ha or 0:.2f} ha"],
        ]
        prop_fmt = []
        for i, row in enumerate(prop_rows):
            if i == 0:
                prop_fmt.append(row)
            else:
                prop_fmt.append([
                    Paragraph(str(row[0]), td_b),
                    Paragraph(str(row[1]), td),
                ])
        story.append(Table(prop_fmt, colWidths=[5*cm, 12.4*cm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE_MEDIO),
            ("GRID", (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [BRANCO, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ])))
        story.append(Spacer(1, 10))

        # ═══════════ MAPA ═══════════
        try:
            map_img = self._gerar_mapa(propriedade)
            if map_img:
                story.append(Paragraph("<b>Vista Aerea - Imagem de Satelite</b>", h2))
                story.append(Spacer(1, 4))
                story.append(Image(map_img, width=17.4*cm, height=9*cm))
                story.append(Paragraph("Satelite: ESRI | Verde: limite do imovel | PRODES: 2021+ vermelho, 2017-2020 laranja, <2017 amarelo", small_center))
        except Exception:
            pass
        story.append(Spacer(1, 12))

        # ═══════════ EMBARGOS ═══════════
        story.append(self._secao_header("3", "Embargos Ambientais"))
        story.append(Spacer(1, 8))

        def _parse_emb(dados, orgao, fonte):
            if not dados: return (orgao, fonte, "NAO VERIFICADO", "-", CINZA)
            emb = dados.get("embargado")
            if emb is True:
                det = dados.get("numero_embargo") or dados.get("motivo") or "Embargo ativo"
                return (orgao, fonte, "EMBARGADO", str(det)[:80], VERMELHO)
            if emb is False:
                return (orgao, fonte, "REGULAR", "Nenhum embargo ativo", VERDE)
            return (orgao, fonte, "NAO VERIFICADO", dados.get("motivo") or "-", CINZA)

        emb_info = [
            _parse_emb(analise.embargo_ibama, "IBAMA", "CTF/IBAMA - PAMGIA"),
            _parse_emb(analise.embargo_semas, "SEMAS-PA", "SEMAS-PA / LDI"),
        ]
        emb_rows = [[Paragraph("<b>Orgao</b>", th), Paragraph("<b>Fonte</b>", th), Paragraph("<b>Status</b>", th_c), Paragraph("<b>Detalhe</b>", th)]]
        for orgao, fonte, status, det, cor in emb_info:
            emb_rows.append([
                Paragraph(orgao, td_b),
                Paragraph(fonte, td_s),
                Paragraph(f'<font color="{cor.hexval()}"><b>{status}</b></font>', ParagraphStyle("ex", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(det, td_s),
            ])
        story.append(Table(emb_rows, colWidths=[3.2*cm, 4*cm, 3*cm, 7.2*cm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE_MEDIO),
            ("GRID", (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [BRANCO, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ])))
        story.append(Spacer(1, 14))

        # ═══════════ AREAS PROTEGIDAS ═══════════
        story.append(self._secao_header("4", "Areas Protegidas e Territorios Especiais"))
        story.append(Spacer(1, 8))

        def _parse_area(dados, tipo, fonte):
            if not dados: return (tipo, fonte, "NAO VERIFICADO", "-", CINZA)
            sobr = dados.get("sobreposicao_detectada")
            if sobr is None: sobr = dados.get("sobreposicao")
            if sobr is True:
                pct = dados.get("percentual_sobreposicao")
                nomes = dados.get("nomes") or []
                nome = ", ".join(nomes[:2]) if nomes else dados.get("nome_area") or "Area"
                det = nome + (f" ({pct:.1f}%)" if pct else "")
                return (tipo, fonte, "SOBREPOSICAO", det[:80], VERMELHO)
            if sobr is False:
                return (tipo, fonte, "REGULAR", f"Fonte: {dados.get('fonte') or fonte}", VERDE)
            return (tipo, fonte, "NAO VERIFICADO", dados.get("motivo_nao_verificado") or "-", CINZA)

        import json as _json
        res_conf = analise.resultado_conformidade or {}
        if isinstance(res_conf, str):
            try: res_conf = _json.loads(res_conf)
            except Exception: res_conf = {}
        quil_raw = res_conf.get("quilombola") or {}
        asset_raw = res_conf.get("assentamento") or {}

        areas_info = [
            _parse_area(analise.sobreposicao_uc, "Unidades de Conservacao", "CNUC/MMA"),
            _parse_area(analise.sobreposicao_ti, "Terras Indigenas", "FUNAI"),
            _parse_area(quil_raw, "Territorios Quilombolas", "INCRA"),
            _parse_area(asset_raw, "Assentamentos Rurais", "INCRA"),
        ]
        ap_rows = [[Paragraph("<b>Tipo</b>", th), Paragraph("<b>Fonte</b>", th), Paragraph("<b>Status</b>", th_c), Paragraph("<b>Detalhe</b>", th)]]
        for tipo, fonte, status, det, cor in areas_info:
            ap_rows.append([
                Paragraph(tipo, td_b),
                Paragraph(fonte, td_s),
                Paragraph(f'<font color="{cor.hexval()}"><b>{status}</b></font>', ParagraphStyle("ax", fontSize=7.5, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(det, td_s),
            ])
        story.append(Table(ap_rows, colWidths=[4*cm, 3.5*cm, 3.2*cm, 6.7*cm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE_MEDIO),
            ("GRID", (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [BRANCO, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ])))
        story.append(Spacer(1, 14))

        # ═══════════ DESMATAMENTO ═══════════
        story.append(self._secao_header("5", "Desmatamento - PRODES/INPE"))
        story.append(Spacer(1, 8))

        desm_det = analise.desmatamento_detectado or False
        desm_ha = analise.area_desmatada_ha or 0
        detalhes_desm = analise.dados_desmatamento or {}
        registros_ano = detalhes_desm.get("registros_por_ano", [])

        desm_rows = [
            [Paragraph("<b>Indicador</b>", th), Paragraph("<b>Resultado</b>", th_c), Paragraph("<b>Detalhe</b>", th)],
            [
                Paragraph("Desmatamento", td_b),
                Paragraph(f'<font color="{"#b71c1c" if desm_det else "#1b5e20"}"><b>{"DETECTADO" if desm_det else "NAO DETECTADO"}</b></font>', td_c),
                Paragraph("PRODES/INPE - TerraBrasilis", td_s),
            ],
            [
                Paragraph("Area suprimida", td_b),
                Paragraph(f"{desm_ha:.2f} ha", td_c),
                Paragraph("Total no periodo 2008-2025", td_s),
            ],
            [
                Paragraph("Metodo", td_b),
                Paragraph("Intersecao espacial", td_c),
                Paragraph("Shapely + PRODES WFS", td_s),
            ],
        ]
        story.append(Table(desm_rows, colWidths=[4.5*cm, 3.5*cm, 9.4*cm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE_MEDIO),
            ("GRID", (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [BRANCO, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ])))

        if registros_ano:
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Registros por Ano:</b>", ParagraphStyle("ra", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO, spaceBefore=4)))
            anos_str = ", ".join(f"{r.get('ano', '?')}: {r.get('area_ha', 0):.1f}ha" for r in registros_ano[:10])
            story.append(Paragraph(anos_str, td_s))

        story.append(Spacer(1, 14))

        # ═══════════ CHECKLIST ═══════════
        story.append(self._secao_header("6", "Checklist de Conformidade"))
        story.append(Spacer(1, 8))

        def _ck(val):
            if val is True: return ("OK", VERDE)
            if val is False: return ("XX", VERMELHO)
            return ("--", CINZA)

        mor_ok = analise.moratorio_soja_conforme
        eudr_ok = analise.eudr_conforme
        ibama_ok = (analise.embargo_ibama or {}).get("embargado") is False if analise.embargo_ibama else None
        semas_ok = (analise.embargo_semas or {}).get("embargado") is False if analise.embargo_semas else None
        uc_ok = (analise.sobreposicao_uc or {}).get("sobreposicao_detectada") is False if analise.sobreposicao_uc else None
        ti_ok = (analise.sobreposicao_ti or {}).get("sobreposicao_detectada") is False if analise.sobreposicao_ti else None
        quil_ok = (not quil_raw.get("sobreposicao")) if isinstance(quil_raw, dict) and quil_raw.get("sobreposicao") is not None else None
        asset_ok = (not asset_raw.get("sobreposicao")) if isinstance(asset_raw, dict) and asset_raw.get("sobreposicao") is not None else None
        trab = res_conf.get("trabalho_escravo") or {}
        trab_ok = (not trab.get("trabalho_escravo", True)) if trab.get("verificado") else None
        bal = res_conf.get("balanco_ambiental") or {}
        bal_ok = bal.get("em_conformidade")

        checklist = [
            ("Moratoria da Soja", mor_ok, "Sem desmatamento pos jul/2008"),
            ("EUDR (2021-2025)", eudr_ok, "Exportacao para Uniao Europeia"),
            ("Embargo IBAMA", ibama_ok, "CTF/IBAMA - PAMGIA"),
            ("Embargo SEMAS-PA", semas_ok, "LDI - SEMAS/SIMLAM"),
            ("Unid. Conservacao", uc_ok, "CNUC/MMA"),
            ("Terra Indigena", ti_ok, "FUNAI"),
            ("Area Quilombola", quil_ok, "INCRA"),
            ("Assentamento", asset_ok, "INCRA SIGEF"),
            ("Trabalho Escravo", trab_ok, "MTE - Lista Suja"),
            ("Balanco RL/APP", bal_ok, f"RL: {bal.get('rl_existente_ha',0):.0f}/{bal.get('rl_exigida_ha',0):.0f} ha"),
            ("Desmatamento", not desm_det, f"{desm_ha:.1f} ha"),
        ]

        ck_rows = [[Paragraph("<b>Item</b>", th), Paragraph("<b>Result.</b>", th_c), Paragraph("<b>Criterio</b>", th)]]
        for nome, val, criterio in checklist:
            ic, cor = _ck(val)
            ck_rows.append([
                Paragraph(nome, td_b),
                Paragraph(f'<font color="{cor.hexval()}"><b>{ic}</b></font>', ParagraphStyle("ci", fontSize=10, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(criterio, td_s),
            ])
        story.append(Table(ck_rows, colWidths=[4.5*cm, 2.2*cm, 10.7*cm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE_MEDIO),
            ("GRID", (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [BRANCO, VERDE_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ])))
        story.append(Spacer(1, 18))

        # ═══════════ AVISO LEGAL ═══════════
        story.append(HRFlowable(width="100%", thickness=1, color=VERDE_MEDIO, spaceAfter=10))
        story.append(Table([[
            Paragraph(
                "<b>AVISO LEGAL:</b> Este laudo foi gerado automaticamente com base em dados publicos oficiais "
                "(SICAR, IBAMA, SEMAS-PA, PRODES/INPE, FUNAI, CNUC/MMA, INCRA). Carater informativo. "
                "Nao substitui analise tecnica ou juridica. Validade: 90 dias. "
                f"Laudo #{id_laudo} | {data_geracao} | {usuario.nome}.",
                aviso
            )
        ]], colWidths=[17.4*cm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), AZUL_CLARO),
            ("BOX", (0,0), (-1,-1), 0.5, AZUL_INFO),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ])))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Fontes: SICAR/MAPA | PRODES/INPE | IBAMA/PAMGIA | SEMAS-PA/LDI | FUNAI | CNUC/MMA | INCRA | MapBiomas",
            ParagraphStyle("fs", fontSize=6.5, fontName="Helvetica", textColor=CINZA, alignment=TA_CENTER)
        ))

        doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
        buffer.seek(0)
        caminho_pdf.write_bytes(buffer.read())
        logger.info(f"Laudo PDF gerado: {caminho_pdf}")
        return str(caminho_pdf), nome_arquivo
