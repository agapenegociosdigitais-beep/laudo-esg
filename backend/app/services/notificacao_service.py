"""Servico de notificacoes Telegram para o Eureka Terra."""

import logging
import httpx

logger = logging.getLogger(__name__)

BOT_TOKEN = "8971848219:AAGNCIwUtulGVAlPdOB62K0SCwcLcLlbyBM"
CHAT_ID = "686152556"


async def notificar(mensagem: str):
    """Envia notificacao para o Telegram."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": mensagem,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code != 200:
                logger.warning(f"Telegram falhou: {resp.text}")
    except Exception as e:
        logger.warning(f"Telegram erro: {e}")


async def notificar_consulta_car(numero_car: str, nome: str, municipio: str, status: str, area: float, fonte: str):
    """Notifica quando um CAR eh consultado."""
    msg = (
        f"<b>🔍 Consulta de CAR</b>\n"
        f"<b>CAR:</b> <code>{numero_car}</code>\n"
        f"<b>Nome:</b> {nome or 'Nao informado'}\n"
        f"<b>Local:</b> {municipio}\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Area:</b> {area:.1f} ha\n"
        f"<b>Fonte:</b> {fonte}"
    )
    await notificar(msg)


async def notificar_pendencias(
    numero_car: str, nome: str, score: float, risco: str,
    desmatamento_detectado: bool, area_desm: float,
    embargo_ibama: bool, embargo_semas: bool,
    anos_prodes: list, eudr_conforme: bool,
):
    """Notifica quando uma analise encontra pendencias."""
    linhas = [f"<b>🚨 Pendencia detectada!</b>"]
    linhas.append(f"<b>CAR:</b> <code>{numero_car}</code>")
    linhas.append(f"<b>Nome:</b> {nome or 'Nao informado'}")
    linhas.append(f"<b>Score ESG:</b> {score:.0f}/100 | <b>Risco:</b> {risco}")
    linhas.append("")
    
    if desmatamento_detectado:
        linhas.append(f"⚠️ <b>Desmatamento:</b> {area_desm:.1f} ha (PRODES)")
        if anos_prodes:
            linhas.append(f"   Anos: {', '.join(str(a) for a in anos_prodes[:5])}")
    if not eudr_conforme:
        linhas.append("❌ <b>EUDR:</b> NAO CONFORME (desmatamento pos 2020)")
    if embargo_ibama:
        linhas.append("🔴 <b>Embargo IBAMA:</b> ATIVO")
    if embargo_semas:
        linhas.append("🔴 <b>Embargo SEMAS-PA:</b> ATIVO")
    
    await notificar("\n".join(linhas))


async def notificar_erro(erro: str, contexto: str = ""):
    """Notifica erros no sistema."""
    msg = f"<b>❌ Erro no Eureka Terra</b>\n{contexto}\n<code>{erro[:200]}</code>"
    await notificar(msg)
