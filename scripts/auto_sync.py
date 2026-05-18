#!/usr/bin/env python3
"""
Auto-sync inteligente — verifica se dados do GeoServer mudaram antes de baixar.
Notifica via email e Telegram sobre sucesso/falha.

Executar via cron: 0 0 * * * python /root/eureka-terra/scripts/auto_sync.py
"""

import json
import logging
import os
import smtplib
import sys
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

import httpx
import sqlalchemy as sa
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

# ═══════════════ CONFIG ═══════════════
DB_URL = os.getenv("DATABASE_URL", "postgresql://eureka:eurekapass@localhost:5432/eureka_db")
GEO_URL = "https://geoserverdw.apps.geoapplications.net/geoserver/wfs/"

# Email (Gmail SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

HEADERS = {"User-Agent": "EurekaTerra/2.0 (auto-sync)"}

# Camadas a sincronizar com data de referencia no GeoServer
LAYERS = [
    ("cache_embargos", "workspace_sicar:vw_sicar_embargos", "Embargos"),
    ("cache_terras_indigenas", "workspace_sicar:vw_sicar_terras_indigenas", "Terras Indigenas"),
    ("cache_unidades_conservacao", "workspace_sicar:vw_sicar_unidades_conservacao", "Unid. Conservacao"),
    ("cache_quilombolas", "workspace_sicar:vw_sicar_areas_quilombolas", "Quilombolas"),
    ("cache_assentamentos", "workspace_sicar:vw_sicar_assentamentos", "Assentamentos"),
    ("cache_prodes", "workspace_sicar:mv_desmatamento_prodes_2008", "PRODES"),
    ("cache_autos_infracao", "workspace_sicar:vw_sicar_autos_de_infracao", "Autos Infracao"),
    ("cache_florestas_publicas", "workspace_sicar:vw_florestas_publicas_2024", "Florestas Publicas"),
    ("cache_alertas_deter", "workspace_fiscalizacao_inteligente:vw_alertas_deter", "Alertas DETER"),
    ("cache_car_ativo", "workspace_sicar:vw_car_ativo", "CAR Ativo"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("auto_sync")

engine = sa.create_engine(DB_URL.replace("+asyncpg", "+psycopg2"))


def notify_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        logger.warning(f"Telegram falhou: {e}")


def notify_email(subject: str, body: str):
    if not SMTP_USER or not NOTIFY_EMAIL:
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        logger.info(f"Email enviado para {NOTIFY_EMAIL}")
    except Exception as e:
        logger.warning(f"Email falhou: {e}")


def get_remote_date(layer: str) -> str | None:
    """Obtem a data_carga mais recente da camada no GeoServer."""
    try:
        resp = httpx.get(
            GEO_URL,
            params={
                "service": "WFS", "version": "2.0.0", "request": "GetFeature",
                "typeName": layer, "outputFormat": "application/json",
                "count": "1", "sortBy": "data_carga D",
            },
            headers=HEADERS, timeout=30, verify=False,
        )
        feats = resp.json().get("features", [])
        if feats:
            return feats[0]["properties"].get("data_carga")
    except Exception as e:
        logger.warning(f"Data remota {layer}: {e}")
    return None


def get_local_date(tabela: str) -> str | None:
    """Obtem a data da ultima sincronizacao da tabela no cache local."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT MAX(data_carga), MAX(sincronizado_em) FROM cache_sync_log WHERE tabela = :t"),
                {"t": tabela},
            ).fetchone()
            if result:
                return result[0] or result[1]
    except Exception:
        pass
    return None


def sync_layer(tabela: str, layer: str, nome: str) -> tuple[int, str]:
    """Sincroniza uma camada. Retorna (registros, status)."""
    remote_date = get_remote_date(layer)
    local_date = get_local_date(tabela)

    if remote_date and local_date and remote_date <= str(local_date):
        logger.info(f"  {nome}: sem alteracoes (remoto={remote_date}, local={local_date})")
        return 0, "sem_alteracoes"

    logger.info(f"  {nome}: baixando (remoto={remote_date}, local={local_date})")
    from scripts.sync_shapefiles import importar_zip, baixar_zip

    try:
        zip_data = baixar_zip(layer)
        n = importar_zip(zip_data, tabela, {})  # colunas mapeadas dentro do sync
        return n, "ok"
    except Exception as e:
        return 0, str(e)[:100]


def main():
    inicio = time.time()
    hostname = os.uname().nodename if hasattr(os, "uname") else "vps"
    logger.info(f"=== Auto-sync Eureka Terra iniciado em {hostname} ===")

    resultados = []
    total_novos = 0
    falhas = 0

    for tabela, layer, nome in LAYERS:
        logger.info(f"-- {nome}")
        try:
            n, status = sync_layer(tabela, layer, nome)
            resultados.append(f"{nome}: {status} ({n} registros)")
            if status == "ok" and n > 0:
                total_novos += n
            if status not in ("ok", "sem_alteracoes"):
                falhas += 1
        except Exception as e:
            resultados.append(f"{nome}: ERRO - {e}")
            falhas += 1

    duracao = time.time() - inicio
    resumo = "\n".join(resultados)

    msg = (
        f"<b>🌱 Eureka Terra — Auto-sync</b>\n"
        f"<b>Servidor:</b> {hostname}\n"
        f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"<b>Duração:</b> {duracao:.0f}s\n"
        f"<b>Novos registros:</b> {total_novos}\n"
        f"<b>Falhas:</b> {falhas}\n\n"
        f"<b>Detalhes:</b>\n{resumo}"
    )

    logger.info(msg)
    notify_telegram(msg)
    notify_email(
        f"Eureka Terra Sync — {total_novos} novos, {falhas} falhas",
        msg.replace("<b>", "").replace("</b>", ""),
    )


if __name__ == "__main__":
    main()
