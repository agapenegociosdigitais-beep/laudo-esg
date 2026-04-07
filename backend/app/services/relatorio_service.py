import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.platypus import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from app.core.config import get_settings
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
settings = get_settings()

# === PALETA DE CORES EUREKA TERRA ===
VERDE_ESCURO   = HexColor("#0d3b1e")
VERDE          = HexColor("#1b5e20")
VERDE_MEDIO    = HexColor("#2e7d32")
VERDE_CLARO    = HexColor("#e8f5e9")
VERDE_ACENTO   = HexColor("#43a047")
DOURADO        = HexColor("#f9a825")
DOURADO_CLARO  = HexColor("#fff8e1")
VERMELHO       = HexColor("#b71c1c")
VERMELHO_CLARO = HexColor("#ffebee")
LARANJA        = HexColor("#e65100")
LARANJA_CLARO  = HexColor("#fff3e0")
CINZA_ESCURO   = HexColor("#212121")
CINZA          = HexColor("#757575")
CINZA_CLARO    = HexColor("#f5f5f5")
CINZA_BORDA    = HexColor("#e0e0e0")
AZUL_INFO      = HexColor("#1565c0")
AZUL_CLARO     = HexColor("#e3f2fd")
BRANCO         = white


class RelatorioService:

    def __init__(self):
        os.makedirs(settings.REPORTS_DIR, exist_ok=True)

    def _estilos(self):
        return {
            "titulo_capa":   ParagraphStyle("titulo_capa",   fontSize=26, textColor=white,        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4),
            "sub_capa":      ParagraphStyle("sub_capa",      fontSize=11, textColor=HexColor("#a5d6a7"), fontName="Helvetica",      alignment=TA_CENTER, spaceAfter=3),
            "tipo_doc":      ParagraphStyle("tipo_doc",      fontSize=13, textColor=DOURADO,       fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6),
            "car_capa":      ParagraphStyle("car_capa",      fontSize=9,  textColor=HexColor("#c8e6c9"), fontName="Helvetica",      alignment=TA_CENTER, spaceAfter=2),
            "info_capa":     ParagraphStyle("info_capa",     fontSize=10, textColor=white,         fontName="Helvetica",      alignment=TA_CENTER, spaceAfter=2),
            "rodape_capa":   ParagraphStyle("rodape_capa",   fontSize=8,  textColor=HexColor("#81c784"), fontName="Helvetica",      alignment=TA_CENTER),
            "h1":            ParagraphStyle("h1",            fontSize=12, textColor=VERDE,         fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6, borderPad=4),
            "h2":            ParagraphStyle("h2",            fontSize=10, textColor=VERDE_MEDIO,   fontName="Helvetica-Bold", spaceBefore=8,  spaceAfter=4),
            "normal":        ParagraphStyle("normal",        fontSize=9,  fontName="Helvetica",    spaceAfter=3,  leading=13, textColor=CINZA_ESCURO),
            "normal_center": ParagraphStyle("normal_center", fontSize=9,  fontName="Helvetica",    spaceAfter=3,  alignment=TA_CENTER, textColor=CINZA_ESCURO),
            "small":         ParagraphStyle("small",         fontSize=7.5,fontName="Helvetica",    textColor=CINZA, spaceAfter=2, leading=11),
            "small_center":  ParagraphStyle("small_center",  fontSize=7.5,fontName="Helvetica",    textColor=CINZA, alignment=TA_CENTER),
            "bold":          ParagraphStyle("bold",          fontSize=9,  fontName="Helvetica-Bold", spaceAfter=3, textColor=CINZA_ESCURO),
            "score_num":     ParagraphStyle("score_num",     fontSize=42, fontName="Helvetica-Bold", alignment=TA_CENTER),
            "score_label":   ParagraphStyle("score_label",   fontSize=8,  fontName="Helvetica",    alignment=TA_CENTER, textColor=CINZA),
            "risco_label":   ParagraphStyle("risco_label",   fontSize=18, fontName="Helvetica-Bold", alignment=TA_CENTER),
            "aviso":         ParagraphStyle("aviso",         fontSize=8,  fontName="Helvetica",    textColor=AZUL_INFO, spaceAfter=2, leading=11, alignment=TA_JUSTIFY),
            "numero_laudo":  ParagraphStyle("numero_laudo",  fontSize=8,  fontName="Helvetica-Bold", textColor=DOURADO, alignment=TA_CENTER),
        }

    def _cor_risco(self, risco):
        return {
            "BAIXO":   (VERDE,        VERDE_CLARO),
            "MEDIO":   (LARANJA,      LARANJA_CLARO),
            "ALTO":    (VERMELHO,     VERMELHO_CLARO),
            "CRITICO": (VERMELHO,     VERMELHO_CLARO),
        }.get((risco or "ALTO").upper(), (VERMELHO, VERMELHO_CLARO))

    def _status_badge(self, status_str):
        s = (status_str or "").upper()
        if s in ("CONFORME", "REGULAR", "SEM SOBREPOSICAO", "SEM SOBREPOSIÇÃO", "OK", "NAO", "NÃO"):
            return ("#1b5e20", "OK " + status_str)
        if s in ("NAO CONFORME", "NÃO CONFORME", "EMBARGADO", "SOBREPOSICAO", "SOBREPOSIÇÃO", "SIM"):
            return ("#b71c1c", "XX " + status_str)
        return ("#757575", "-- " + status_str)

    def _secao_header(self, numero, titulo, s):
        dados = [[
            Paragraph(f"{numero}", ParagraphStyle("n", fontSize=11, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph(titulo.upper(), ParagraphStyle("t", fontSize=10, fontName="Helvetica-Bold", textColor=white, alignment=TA_LEFT)),
        ]]
        t = Table(dados, colWidths=[1.0*cm, 16*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), VERDE_MEDIO),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (0,0),   8),
            ("LEFTPADDING",   (1,0), (1,0),   10),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ROUNDEDCORNERS",(0,0), (-1,-1), [3,3,3,3]) if hasattr(TableStyle, "ROUNDEDCORNERS") else ("BOX",(0,0),(-1,-1),0,VERDE_MEDIO),
        ]))
        return t

    async def gerar_pdf(self, analise: Analise, propriedade: Propriedade, usuario: Usuario):
        car_safe = propriedade.numero_car.replace("/", "-")[:30]
        id_laudo = uuid.uuid4().hex[:8].upper()
        nome_arquivo = f"relatorio_{car_safe}_{id_laudo.lower()}.pdf"
        caminho_pdf = Path(settings.REPORTS_DIR) / nome_arquivo

        buffer = BytesIO()
        W, H = A4

        def _rodape_pagina(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(VERDE_ESCURO)
            canvas.rect(0, 0, W, 1.1*cm, fill=1, stroke=0)
            canvas.setFillColor(HexColor("#a5d6a7"))
            canvas.setFont("Helvetica", 7)
            canvas.drawString(2*cm, 0.38*cm, f"Eureka Terra | Laudo #{id_laudo} | {propriedade.numero_car}")
            canvas.drawRightString(W - 2*cm, 0.38*cm, f"Pág. {doc.page} | Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Validade: 90 dias")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=1.5*cm, bottomMargin=1.8*cm,
            title=f"Laudo ESG #{id_laudo} - {propriedade.numero_car}",
            author="Eureka Terra",
            subject="Auditoria Ambiental ESG",
        )

        s = self._estilos()
        story = []

        def _limpa(txt):
            if not txt: return txt
            return str(txt).replace('\u00e9', 'e').replace('\u00e1', 'a').replace('\u00e3', 'a').replace('\u00f4', 'o').replace('\u00ea', 'e').replace('\u00ed', 'i').replace('\u00fa', 'u').replace('\u00e7', 'c').replace('\u00c1', 'A').replace('\u00c9', 'E').replace('\u00cd', 'I').replace('\u00d3', 'O').replace('\u00da', 'U').replace('\u00c3', 'A').replace('\u00d4', 'O').replace('\u00ca', 'E').replace('\u00c7', 'C').replace('\xe9', 'e').replace('\xe1', 'a').replace('\xe3', 'a').replace('\xf4', 'o').replace('\xea', 'e').replace('\xed', 'i').replace('\xfa', 'u').replace('\xe7', 'c')

        def _s(txt):
            if not isinstance(txt, str): return str(txt) if txt else ''
            acentos = {'á':'a','à':'a','ã':'a','â':'a','é':'e','ê':'e','í':'i','ó':'o','ô':'o','õ':'o','ú':'u','ç':'c','Á':'A','À':'A','Ã':'A','Â':'A','É':'E','Ê':'E','Í':'I','Ó':'O','Ô':'O','Õ':'O','Ú':'U','Ç':'C','–':'-','·':'|'}
            for k, v in acentos.items():
                txt = txt.replace(k, v)
            return txt
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
        score = analise.score_esg or 0
        risco = (analise.nivel_risco or "ALTO").upper()
        cor_risco, bg_risco = self._cor_risco(risco)

        # ===================== CAPA =====================
        capa_rows = [
            [Paragraph(" ", ParagraphStyle("esp0", fontSize=14))],
            [Paragraph("EUREKA TERRA", s["titulo_capa"])],
            [Paragraph(" ", ParagraphStyle("esp1", fontSize=6))],
            [Paragraph("Plataforma de Auditoria Ambiental e Conformidade ESG", s["sub_capa"])],
            [Paragraph(" ", ParagraphStyle("esp2", fontSize=10))],
            [Paragraph("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", ParagraphStyle("hr1", fontSize=7, textColor=DOURADO, alignment=TA_CENTER))],
            [Paragraph(" ", ParagraphStyle("esp3", fontSize=6))],
            [Paragraph("LAUDO DE CONFORMIDADE AMBIENTAL", s["tipo_doc"])],
            [Paragraph("Auditoria ESG  |  Propriedade Rural  |  Amazonia Legal", ParagraphStyle("sl2", fontSize=9, textColor=HexColor("#81c784"), fontName="Helvetica", alignment=TA_CENTER))],
            [Paragraph(" ", ParagraphStyle("esp4", fontSize=12))],
            [Paragraph(f"No  {id_laudo}", s["numero_laudo"])],
            [Paragraph(" ", ParagraphStyle("esp5", fontSize=6))],
            [Paragraph(f"CAR: {propriedade.numero_car}", s["car_capa"])],
            [Paragraph(f"Imovel: {_s(propriedade.nome_propriedade) or 'Imovel Rural'}", s["info_capa"])],
            [Paragraph(f"Municipio / UF: {_s(propriedade.municipio)} - {_s(propriedade.estado)}", s["info_capa"])],
            [Paragraph(f"Area: {propriedade.area_ha or 0:.1f} ha  |  Bioma: {_s(propriedade.bioma) or 'Amazonia'}", s["info_capa"])],
            [Paragraph(" ", ParagraphStyle("esp6", fontSize=12))],
            [Paragraph("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", ParagraphStyle("hr2", fontSize=5, textColor=HexColor("#388e3c"), alignment=TA_CENTER))],
            [Paragraph(" ", ParagraphStyle("esp7", fontSize=6))],
            [Paragraph(f"Gerado em {data_geracao}  |  Solicitante: {usuario.nome}", s["rodape_capa"])],
            [Paragraph("Validade: 90 dias  |  Uso restrito ao imovel analisado", s["rodape_capa"])],
            [Paragraph(" ", ParagraphStyle("esp8", fontSize=14))],
        ]
        t_capa = Table(capa_rows, colWidths=[17*cm])
        t_capa.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), VERDE_ESCURO),
            ("TOPPADDING",    (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 10),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ]))
        story.append(t_capa)
        story.append(Spacer(1, 16))

        # ===================== SCORE ESG =====================
        story.append(self._secao_header("1", "Score ESG e Resultado da Auditoria", s))
        story.append(Spacer(1, 8))

        icone_risco = {"BAIXO": "OK", "MEDIO": "!", "ALTO": "XX", "CRITICO": "XX"}.get(risco, "!")
        score_rows = [
            [
                Paragraph(f'<font color="{cor_risco.hexval()}">{score:.0f}</font>', ParagraphStyle("sn", fontSize=48, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f'<font color="{cor_risco.hexval()}">{risco}</font>', ParagraphStyle("rn", fontSize=22, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            ],
            [
                Paragraph("Score ESG / 100", s["score_label"]),
                Paragraph("Nivel de Risco Ambiental", s["score_label"]),
            ],
        ]
        t_score = Table(score_rows, colWidths=[8.5*cm, 8.5*cm])
        t_score.setStyle(TableStyle([
            ("BOX",           (0,0), (-1,-1), 1.5, cor_risco),
            ("INNERGRID",     (0,0), (-1,-1), 0.5, CINZA_BORDA),
            ("BACKGROUND",    (0,0), (-1,-1), bg_risco),
            ("TOPPADDING",    (0,0), (-1,-1), 14),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_score)
        story.append(Spacer(1, 10))

        # RESUMO CONFORMIDADE
        def status_txt(val):
            if val is True:  return "CONFORME"
            if val is False: return "NÃO CONFORME"
            return "NAO VERIFICADO"

        def cor_status(val):
            if val is True:  return VERDE
            if val is False: return VERMELHO
            return CINZA

        conf_header = [
            Paragraph("Verificacao", ParagraphStyle("ch", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("Status", ParagraphStyle("ch", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("Detalhe", ParagraphStyle("ch", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
        ]
        conf_rows = [conf_header]
        itens_conf = [
            ("Moratorio da Soja (jul/2008)", analise.moratorio_soja_conforme, _s(analise.moratorio_soja_detalhe) or "Verificado via PRODES/INPE"),
            ("EUDR - Reg. UE 2023/1115 (dez/2020)", analise.eudr_conforme, _s(analise.eudr_detalhe) or "Verificado via Copernicus/ESA"),
        ]
        for nome, val, detalhe in itens_conf:
            c = cor_status(val)
            conf_rows.append([
                Paragraph(nome, ParagraphStyle("cn", fontSize=8, fontName="Helvetica", textColor=CINZA_ESCURO)),
                Paragraph(f'<font color="{c.hexval()}"><b>{status_txt(val)}</b></font>', ParagraphStyle("cs", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(detalhe[:100], ParagraphStyle("cd", fontSize=7.5, fontName="Helvetica", textColor=CINZA)),
            ])

        t_conf = Table(conf_rows, colWidths=[5.5*cm, 3.5*cm, 8*cm])
        t_conf.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), VERDE_MEDIO),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("GRID",          (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, VERDE_CLARO]),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_conf)
        story.append(Spacer(1, 16))

        # ===================== DADOS DA PROPRIEDADE =====================
        story.append(self._secao_header("2", "Identificacao da Propriedade Rural", s))
        story.append(Spacer(1, 8))

        prop_rows = [
            [Paragraph("Campo", ParagraphStyle("ph", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
             Paragraph("Valor", ParagraphStyle("ph", fontSize=8, fontName="Helvetica-Bold", textColor=white))],
            ["Numero CAR", propriedade.numero_car],
            ["Status CAR / SICAR", _s(propriedade.status_car) or "ATIVO"],
            ["Nome do Imovel", _s(propriedade.nome_propriedade) or "Imovel Rural"],
            ["Municipio / UF", f"{_s(propriedade.municipio)} / {_s(propriedade.estado)}"],
            ["Bioma", _s(propriedade.bioma) or "Amazonia"],
            ["Area Declarada", f"{propriedade.area_ha or 0:.2f} ha"],
            ["Modulos Fiscais", f"{((propriedade.area_ha or 0) / 65):.2f} MF (ref. 65 ha/MF - Pará)"],
        ]
        prop_fmt = []
        for i, row in enumerate(prop_rows):
            if i == 0:
                prop_fmt.append(row)
            else:
                prop_fmt.append([
                    Paragraph(str(row[0]), ParagraphStyle("pk", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)),
                    Paragraph(str(row[1]), ParagraphStyle("pv", fontSize=8, fontName="Helvetica", textColor=CINZA_ESCURO)),
                ])
        t_prop = Table(prop_fmt, colWidths=[5*cm, 12*cm])
        t_prop.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), VERDE_MEDIO),
            ("GRID",          (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_prop)
        story.append(Spacer(1, 16))

        # ===================== EMBARGOS =====================
        story.append(self._secao_header("3", "Embargos Ambientais", s))
        story.append(Spacer(1, 8))

        def parse_embargo(dados, orgao, fonte):
            if not dados:
                return (orgao, fonte, "NAO VERIFICADO", "-", CINZA, CINZA_CLARO)
            if dados.get("embargado") is True:
                det = dados.get("numero_embargo") or dados.get("motivo") or "Embargo ativo registrado"
                return (orgao, fonte, "EMBARGADO", det[:80], VERMELHO, VERMELHO_CLARO)
            if dados.get("embargado") is False:
                return (orgao, fonte, "REGULAR", "Nenhum embargo ativo encontrado", VERDE, VERDE_CLARO)
            return (orgao, fonte, "NAO VERIFICADO", dados.get("motivo") or "Servico indisponivel", CINZA, CINZA_CLARO)

        embargos_info = [
            parse_embargo(analise.embargo_ibama, "IBAMA Federal", "CTF/IBAMA - PAMGIA"),
            parse_embargo(analise.embargo_semas, "SEMAS-PA Estadual", "SEMAS-PA / SIMLAM / LDI"),
        ]

        emb_header = [
            Paragraph("Orgao", ParagraphStyle("eh", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("Fonte", ParagraphStyle("eh", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("Status", ParagraphStyle("eh", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("Detalhe", ParagraphStyle("eh", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
        ]
        emb_rows = [emb_header]
        for i, (orgao, fonte, status, det, cor, bg) in enumerate(embargos_info):
            emb_rows.append([
                Paragraph(orgao, ParagraphStyle("eo", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)),
                Paragraph(fonte, ParagraphStyle("ef", fontSize=7.5, fontName="Helvetica", textColor=CINZA)),
                Paragraph(f'<font color="{cor.hexval()}"><b>{status}</b></font>', ParagraphStyle("es", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(det, ParagraphStyle("ed", fontSize=7.5, fontName="Helvetica", textColor=CINZA_ESCURO)),
            ])

        t_emb = Table(emb_rows, colWidths=[3.5*cm, 4*cm, 3*cm, 6.5*cm])
        t_emb.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), VERDE_MEDIO),
            ("GRID",          (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_emb)
        story.append(Spacer(1, 16))

        # ===================== AREAS PROTEGIDAS =====================
        story.append(self._secao_header("4", "Areas Protegidas e Territorios Especiais", s))
        story.append(Spacer(1, 8))

        def parse_area(dados, tipo, fonte):
            if not dados:
                return (tipo, fonte, "NAO VERIFICADO", "-", CINZA, CINZA_CLARO)
            # Suporta ambos: sobreposicao_detectada (UC/TI) e sobreposicao (INCRA)
            sobr = dados.get("sobreposicao_detectada")
            if sobr is None:
                sobr = dados.get("sobreposicao")
            if sobr is True:
                pct = dados.get("percentual_sobreposicao")
                nomes = dados.get("nomes") or []
                nome = ", ".join(nomes[:2]) if nomes else dados.get("nome_area") or "Area identificada"
                total = dados.get("total", 0)
                det = f"{nome}" + (f" ({total} registro(s))" if total else "")
                return (tipo, fonte, "SOBREPOSICAO", det[:80], VERMELHO, VERMELHO_CLARO)
            if sobr is False:
                fonte_real = dados.get("fonte") or fonte
                return (tipo, fonte, "SEM SOBREPOSICAO", f"Fonte: {fonte_real}", VERDE, VERDE_CLARO)
            return (tipo, fonte, "NAO VERIFICADO", dados.get("motivo_nao_verificado") or "-", CINZA, CINZA_CLARO)

        # Extrai dados de quilombola e assentamento do resultado_conformidade
        import json as _json
        res_conf = analise.resultado_conformidade or {}
        if isinstance(res_conf, str):
            try: res_conf = _json.loads(res_conf)
            except: res_conf = {}
        # Dados reais do resultado_conformidade
        quilombola_raw = res_conf.get("quilombola")
        assentamento_raw = res_conf.get("assentamento")
        if quilombola_raw is None:
            quilombola_raw = {"sobreposicao": None, "motivo_nao_verificado": "Nao verificado"}
        if assentamento_raw is None:
            assentamento_raw = {"sobreposicao": None, "motivo_nao_verificado": "Nao verificado"}
        areas_info = [
            parse_area(analise.sobreposicao_uc,  "Unidades de Conservacao",   "CNUC / Ministerio do Meio Ambiente"),
            parse_area(analise.sobreposicao_ti,  "Terras Indigenas",          "FUNAI - Terras Homologadas"),
            parse_area(quilombola_raw, "Territorios Quilombolas", "INCRA SIGEF - Portaria"),
            parse_area(assentamento_raw, "Assentamentos Rurais", "INCRA SIGEF - Projetos"),
        ]

        ap_header = [
            Paragraph("Tipo de Area", ParagraphStyle("ah", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("Fonte", ParagraphStyle("ah", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("Status", ParagraphStyle("ah", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("Detalhe", ParagraphStyle("ah", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
        ]
        ap_rows = [ap_header]
        for tipo, fonte, status, det, cor, bg in areas_info:
            ap_rows.append([
                Paragraph(tipo, ParagraphStyle("at", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)),
                Paragraph(fonte, ParagraphStyle("af", fontSize=7.5, fontName="Helvetica", textColor=CINZA)),
                Paragraph(f'<font color="{cor.hexval()}"><b>{status}</b></font>', ParagraphStyle("as2", fontSize=7.5, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(det, ParagraphStyle("ad", fontSize=7.5, fontName="Helvetica", textColor=CINZA_ESCURO)),
            ])

        t_ap = Table(ap_rows, colWidths=[4*cm, 4.5*cm, 3.5*cm, 5*cm])
        t_ap.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), VERDE_MEDIO),
            ("GRID",          (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_ap)
        story.append(Spacer(1, 16))

        # ===================== DESMATAMENTO =====================
        story.append(self._secao_header("5", "Monitoramento de Desmatamento - PRODES/INPE", s))
        story.append(Spacer(1, 8))

        desm_detectado = analise.desmatamento_detectado or False
        area_desm = analise.area_desmatada_ha or 0.0
        cor_desm = VERMELHO if desm_detectado else VERDE
        status_desm = "DETECTADO" if desm_detectado else "NÃO DETECTADO"

        desm_rows = [
            [Paragraph("Indicador", ParagraphStyle("dh", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
             Paragraph("Resultado", ParagraphStyle("dh", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
             Paragraph("Observacao", ParagraphStyle("dh", fontSize=8, fontName="Helvetica-Bold", textColor=white))],
            [Paragraph("Desmatamento Detectado", ParagraphStyle("di", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)),
             Paragraph(f'<font color="{cor_desm.hexval()}"><b>{status_desm}</b></font>', ParagraphStyle("dr", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER)),
             Paragraph("Fonte: PRODES/INPE - Monitoramento por satelite", ParagraphStyle("do", fontSize=7.5, fontName="Helvetica", textColor=CINZA))],
            [Paragraph("Area Suprimida", ParagraphStyle("di", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)),
             Paragraph(f"{area_desm:.2f} ha", ParagraphStyle("dr", fontSize=8, fontName="Helvetica", alignment=TA_CENTER)),
             Paragraph("Hectares com supressao confirmada no periodo", ParagraphStyle("do", fontSize=7.5, fontName="Helvetica", textColor=CINZA))],
            [Paragraph("Periodo de Referencia", ParagraphStyle("di", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)),
             Paragraph("2008 - 2024", ParagraphStyle("dr", fontSize=8, fontName="Helvetica", alignment=TA_CENTER)),
             Paragraph("Serie historica completa PRODES desde Moratorio da Soja", ParagraphStyle("do", fontSize=7.5, fontName="Helvetica", textColor=CINZA))],
            [Paragraph("Cobertura", ParagraphStyle("di", fontSize=8, fontName="Helvetica-Bold", textColor=CINZA_ESCURO)),
             Paragraph("Amazonia Legal", ParagraphStyle("dr", fontSize=8, fontName="Helvetica", alignment=TA_CENTER)),
             Paragraph("Resolucao espacial: 30m (Landsat) - TerraBrasilis/INPE", ParagraphStyle("do", fontSize=7.5, fontName="Helvetica", textColor=CINZA))],
        ]
        t_desm = Table(desm_rows, colWidths=[4.5*cm, 3.5*cm, 9*cm])
        t_desm.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), VERDE_MEDIO),
            ("GRID",          (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_desm)
        story.append(Spacer(1, 16))

        # ===================== CHECKLIST FINAL =====================
        story.append(self._secao_header("6", "Checklist de Conformidade ESG - Resumo Executivo", s))
        story.append(Spacer(1, 8))

        def check(val):
            if val is True:  return ("CONF", VERDE)
            if val is False: return ("ALERTA", VERMELHO)
            return ("N/A", CINZA)

        moratorio_ok   = analise.moratorio_soja_conforme
        eudr_ok        = analise.eudr_conforme
        ibama_ok       = (analise.embargo_ibama or {}).get("embargado") is False if analise.embargo_ibama else None
        semas_ok       = (analise.embargo_semas or {}).get("embargado") is False if analise.embargo_semas else None
        uc_ok          = (analise.sobreposicao_uc or {}).get("sobreposicao_detectada") is False if analise.sobreposicao_uc else None
        ti_ok          = (analise.sobreposicao_ti or {}).get("sobreposicao_detectada") is False if analise.sobreposicao_ti else None
        desm_ok        = not desm_detectado

        # Dados extras do resultado_conformidade
        balanco = res_conf.get("balanco_ambiental") or {}
        trab_escravo = res_conf.get("trabalho_escravo") or {}
        rl_exigida = balanco.get("rl_exigida_ha", 0.0)
        rl_existente = balanco.get("rl_existente_ha", 0.0)
        balanco_ok2 = balanco.get("em_conformidade")
        trab_ok2 = (not trab_escravo.get("trabalho_escravo", True)) if trab_escravo.get("verificado") else None
        quil_sob = quilombola_raw.get("sobreposicao") if isinstance(quilombola_raw, dict) else None
        quil_ok2 = (not quil_sob) if quil_sob is not None else None
        asset_sob = assentamento_raw.get("sobreposicao") if isinstance(assentamento_raw, dict) else None
        asset_ok2 = (not asset_sob) if asset_sob is not None else None

        checklist = [
            ("Moratorio da Soja", moratorio_ok, "Ausencia de desmatamento pos jul/2008 - PRODES/INPE"),
            ("EUDR (Reg. UE 2023/1115)", eudr_ok, "Ausencia de desmatamento pos dez/2020 - Exportacao UE"),
            ("Embargo IBAMA", ibama_ok, "Sem embargo ativo no CTF/IBAMA - PAMGIA"),
            ("Embargo SEMAS-PA", semas_ok, "Sem embargo ativo na LDI - SEMAS/SIMLAM"),
            ("Unidade de Conservacao", uc_ok, "Sem sobreposicao com UC federal/estadual - CNUC"),
            ("Terra Indigena", ti_ok, "Sem sobreposicao com TI homologada - FUNAI"),
            ("Territorio Quilombola", quil_ok2, "Sem sobreposicao com territorio quilombola - INCRA"),
            ("Assentamento Rural", asset_ok2, "Verificacao de sobreposicao com assentamentos - INCRA SIGEF"),
            ("Lista Trabalho Escravo", trab_ok2, "Ausente na lista suja do MTE / Portal da Transparencia"),
            ("Balanco RL/APP", balanco_ok2, f"RL exigida: {rl_exigida:.1f}ha | RL existente: {rl_existente:.1f}ha"),
            ("Desmatamento PRODES", desm_ok, "Sem supressao detectada no periodo de referencia"),
        ]

        ck_header = [
            Paragraph("Item de Conformidade", ParagraphStyle("ckh", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("Resultado", ParagraphStyle("ckh", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("Criterio Verificado", ParagraphStyle("ckh", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
        ]
        ck_rows = [ck_header]
        for nome, val, criterio in checklist:
            ic, cor = check(val)
            ck_rows.append([
                Paragraph(nome, ParagraphStyle("ckn", fontSize=8, fontName="Helvetica", textColor=CINZA_ESCURO)),
                Paragraph(f'<font color="{cor.hexval()}"><b>{ic}</b></font>', ParagraphStyle("cki", fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(criterio, ParagraphStyle("ckc", fontSize=7.5, fontName="Helvetica", textColor=CINZA)),
            ])

        t_ck = Table(ck_rows, colWidths=[5*cm, 2.5*cm, 9.5*cm])
        t_ck.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), VERDE_MEDIO),
            ("GRID",          (0,0), (-1,-1), 0.4, CINZA_BORDA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, VERDE_CLARO]),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t_ck)
        story.append(Spacer(1, 20))

        # ===================== RODAPÉ LEGAL =====================
        story.append(HRFlowable(width="100%", thickness=1, color=VERDE_MEDIO, spaceAfter=8))
        aviso_rows = [[
            Paragraph(
                "<b>AVISO LEGAL:</b> Este laudo e gerado automaticamente pela plataforma Eureka Terra com base em dados publicos oficiais "
                "(SICAR/MAPA, IBAMA/PAMGIA, SEMAS-PA/LDI, PRODES/INPE, FUNAI, CNUC/MMA, INCRA/SIGEF) e tem carater informativo. "
                "Nao substitui análise tecnica ou juridica especializada. Validade: 90 dias a partir da emissao. "
                f"Laudo No {id_laudo} | Emitido em {data_geracao} | Solicitante: {usuario.nome}.",
                s["aviso"]
            )
        ]]
        t_aviso = Table(aviso_rows, colWidths=[17*cm])
        t_aviso.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), AZUL_CLARO),
            ("BOX",           (0,0), (-1,-1), 0.5, AZUL_INFO),
            ("TOPPADDING",    (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ]))
        story.append(t_aviso)
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "Fontes: SICAR/MAPA | PRODES/INPE | IBAMA/PAMGIA | SEMAS-PA/LDI | FUNAI/GeoServer | CNUC/MMA | INCRA/SIGEF | MapBiomas | Copernicus/ESA",
            ParagraphStyle("fs", fontSize=6.5, fontName="Helvetica", textColor=CINZA, alignment=TA_CENTER)
        ))

        doc.build(story, onFirstPage=_rodape_pagina, onLaterPages=_rodape_pagina)
        buffer.seek(0)
        caminho_pdf.write_bytes(buffer.read())
        logger.info(f"Laudo PDF gerado: {caminho_pdf}")
        return str(caminho_pdf), nome_arquivo
