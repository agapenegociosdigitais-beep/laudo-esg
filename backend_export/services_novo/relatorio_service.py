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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.platypus import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.core.config import get_settings
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
settings = get_settings()

VERDE = HexColor("#1b5e20")
VERDE_CLARO = HexColor("#e8f5e9")
VERDE_MEDIO = HexColor("#2e7d32")
VERMELHO = HexColor("#b71c1c")
VERMELHO_CLARO = HexColor("#ffebee")
AMARELO = HexColor("#f9a825")
AMARELO_CLARO = HexColor("#fff8e1")
CINZA = HexColor("#757575")
CINZA_CLARO = HexColor("#f5f5f5")
CINZA_BORDA = HexColor("#e0e0e0")


class RelatorioService:

    def __init__(self):
        os.makedirs(settings.REPORTS_DIR, exist_ok=True)

    def _estilos(self):
        styles = getSampleStyleSheet()
        return {
            "titulo": ParagraphStyle("titulo", fontSize=18, textColor=white, fontName="Helvetica-Bold", spaceAfter=6),
            "subtitulo": ParagraphStyle("subtitulo", fontSize=10, textColor=white, fontName="Helvetica", spaceAfter=4),
            "h1": ParagraphStyle("h1", fontSize=13, textColor=VERDE, fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=8),
            "normal": ParagraphStyle("normal", fontSize=10, fontName="Helvetica", spaceAfter=4, leading=14),
            "small": ParagraphStyle("small", fontSize=8, fontName="Helvetica", textColor=CINZA, spaceAfter=2),
            "bold": ParagraphStyle("bold", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4),
            "center": ParagraphStyle("center", fontSize=10, fontName="Helvetica", alignment=TA_CENTER),
            "score": ParagraphStyle("score", fontSize=36, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=VERDE),
        }

    def _badge(self, texto, cor_bg, cor_texto=None):
        cor = cor_texto or white
        return f'<font color="{cor_bg}">[{texto}]</font>'

    async def gerar_pdf(self, analise: Analise, propriedade: Propriedade, usuario: Usuario):
        car_safe = propriedade.numero_car.replace("/", "-")[:30]
        nome_arquivo = f"relatorio_{car_safe}_{uuid.uuid4().hex[:8]}.pdf"
        caminho_pdf = Path(settings.REPORTS_DIR) / nome_arquivo

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
            title=f"Relatorio ESG - {propriedade.numero_car}"
        )

        s = self._estilos()
        story = []
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")

        # CAPA
        capa_data = [
            [Paragraph("EUREKA TERRA", s["titulo"])],
            [Paragraph("Plataforma de Analise ESG para Propriedades Rurais", s["subtitulo"])],
            [Spacer(1, 20)],
            [Paragraph("Relatorio de Conformidade Ambiental", ParagraphStyle("ct", fontSize=14, textColor=white, fontName="Helvetica-Bold"))],
            [Paragraph(propriedade.numero_car, ParagraphStyle("car", fontSize=11, textColor=white, fontName="Helvetica", spaceAfter=20))],
            [Paragraph(f"Propriedade: {propriedade.nome_propriedade or 'Nao informado'}", s["subtitulo"])],
            [Paragraph(f"Municipio/UF: {propriedade.municipio} - {propriedade.estado}", s["subtitulo"])],
            [Paragraph(f"Area: {propriedade.area_ha or 0:.1f} ha | Bioma: {propriedade.bioma or '-'}", s["subtitulo"])],
            [Spacer(1, 10)],
            [Paragraph(f"Gerado em {data_geracao} | Solicitante: {usuario.nome}", ParagraphStyle("rodape_capa", fontSize=8, textColor=HexColor("#cccccc"), fontName="Helvetica"))],
        ]
        t_capa = Table(capa_data, colWidths=[17*cm])
        t_capa.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), VERDE),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 20),
            ("RIGHTPADDING", (0,0), (-1,-1), 20),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [VERDE]),
        ]))
        story.append(t_capa)
        story.append(Spacer(1, 20))

        # SCORE ESG
        story.append(Paragraph("1. Score ESG e Resumo", s["h1"]))
        score = analise.score_esg or 0
        risco = analise.nivel_risco or "ALTO"
        cor_risco = {"BAIXO": "#1b5e20", "MEDIO": "#e65100", "ALTO": "#bf360c", "CRITICO": "#b71c1c"}.get(risco, "#bf360c")

        score_data = [
            [
                Paragraph(f'<font color="{cor_risco}"><b>{score:.0f}/100</b></font>', ParagraphStyle("sc", fontSize=28, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f'<font color="{cor_risco}"><b>{risco}</b></font>', ParagraphStyle("rc", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            ],
            [
                Paragraph("Score ESG", ParagraphStyle("sl", fontSize=9, fontName="Helvetica", alignment=TA_CENTER, textColor=CINZA)),
                Paragraph("Nivel de Risco", ParagraphStyle("rl", fontSize=9, fontName="Helvetica", alignment=TA_CENTER, textColor=CINZA)),
            ],
        ]
        t_score = Table(score_data, colWidths=[8.5*cm, 8.5*cm])
        t_score.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 1, CINZA_BORDA),
            ("INNERGRID", (0,0), (-1,-1), 0.5, CINZA_BORDA),
            ("BACKGROUND", (0,0), (-1,-1), CINZA_CLARO),
            ("TOPPADDING", (0,0), (-1,-1), 12),
            ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ]))
        story.append(t_score)
        story.append(Spacer(1, 12))

        # CONFORMIDADE
        def status_txt(val):
            if val is True: return "CONFORME"
            if val is False: return "NAO CONFORME"
            return "NAO VERIFICADO"

        conf_data = [
            ["Verificacao", "Status", "Detalhe"],
            ["Moratorio da Soja", status_txt(analise.moratorio_soja_conforme), analise.moratorio_soja_detalhe or "-"],
            ["EUDR (UE)", status_txt(analise.eudr_conforme), analise.eudr_detalhe or "-"],
        ]
        t_conf = Table(conf_data, colWidths=[4*cm, 3.5*cm, 9.5*cm])
        t_conf.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.5, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(t_conf)
        story.append(Spacer(1, 16))

        # DADOS DA PROPRIEDADE
        story.append(Paragraph("2. Dados da Propriedade", s["h1"]))
        prop_data = [
            ["Campo", "Valor"],
            ["Numero CAR", propriedade.numero_car],
            ["Status CAR", propriedade.status_car or "ATIVO"],
            ["Nome", propriedade.nome_propriedade or "-"],
            ["Municipio / UF", f"{propriedade.municipio} / {propriedade.estado}"],
            ["Bioma", propriedade.bioma or "-"],
            ["Area Declarada", f"{propriedade.area_ha or 0:.2f} ha"],
        ]
        t_prop = Table(prop_data, colWidths=[5*cm, 12*cm])
        t_prop.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.5, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(t_prop)
        story.append(Spacer(1, 16))

        # EMBARGOS
        story.append(Paragraph("3. Embargos Ambientais", s["h1"]))
        def linha_embargo(dados, orgao):
            if not dados:
                return [orgao, "Nao verificado", "-"]
            if dados.get("embargado") is True:
                return [orgao, "EMBARGADO", dados.get("numero_embargo") or dados.get("motivo") or "-"]
            if dados.get("embargado") is False:
                return [orgao, "Regular", "Nenhum embargo ativo"]
            return [orgao, "Nao verificado", dados.get("motivo") or "-"]

        emb_data = [
            ["Orgao", "Status", "Detalhe"],
            linha_embargo(analise.embargo_ibama, "IBAMA Federal"),
            linha_embargo(analise.embargo_semas, "SEMAS-PA Estadual"),
        ]
        t_emb = Table(emb_data, colWidths=[4*cm, 3.5*cm, 9.5*cm])
        t_emb.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.5, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(t_emb)
        story.append(Spacer(1, 16))

        # AREAS PROTEGIDAS
        story.append(Paragraph("4. Areas Protegidas", s["h1"]))
        def linha_area(dados, tipo):
            if not dados:
                return [tipo, "Nao verificado", "-"]
            if dados.get("sobreposicao_detectada") is True:
                pct = dados.get("percentual_sobreposicao")
                detalhe = dados.get("nome_area") or "-"
                if pct: detalhe += f" ({pct:.1f}%)"
                return [tipo, "SOBREPOSICAO", detalhe]
            if dados.get("sobreposicao_detectada") is False:
                return [tipo, "Sem sobreposicao", f'Fonte: {dados.get("fonte", "-")}']
            return [tipo, "Nao verificado", dados.get("motivo_nao_verificado") or "-"]

        ap_data = [
            ["Tipo", "Status", "Detalhe"],
            linha_area(analise.sobreposicao_uc, "Unidades de Conservacao"),
            linha_area(analise.sobreposicao_ti, "Terras Indigenas"),
        ]
        t_ap = Table(ap_data, colWidths=[5*cm, 4*cm, 8*cm])
        t_ap.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.5, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(t_ap)
        story.append(Spacer(1, 16))

        # DESMATAMENTO
        story.append(Paragraph("5. Monitoramento de Desmatamento", s["h1"]))
        desm = "SIM" if analise.desmatamento_detectado else "NAO"
        area_desm = f"{analise.area_desmatada_ha or 0:.2f} ha"
        desm_data = [
            ["Indicador", "Resultado"],
            ["Desmatamento Detectado", desm],
            ["Area Suprimida", area_desm],
            ["Periodo de Referencia", "2008-2024 (PRODES/INPE)"],
        ]
        t_desm = Table(desm_data, colWidths=[7*cm, 10*cm])
        t_desm.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.5, CINZA_BORDA),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(t_desm)
        story.append(Spacer(1, 16))

        # RODAPE
        story.append(HRFlowable(width="100%", thickness=1, color=CINZA_BORDA))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Relatorio gerado automaticamente pela plataforma Eureka Terra em {data_geracao}.", s["small"]))
        story.append(Paragraph("Este relatorio tem carater informativo e nao substitui analise tecnica ou juridica especializada.", s["small"]))

        doc.build(story)
        buffer.seek(0)
        caminho_pdf.write_bytes(buffer.read())
        logger.info(f"Relatorio PDF gerado: {caminho_pdf}")
        return str(caminho_pdf), nome_arquivo