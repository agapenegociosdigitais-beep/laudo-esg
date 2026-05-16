#!/usr/bin/env python3
"""
Baixa TODOS os shapefiles do GeoServer nacional unificado (SEMAS-PA / SICAR).
Fonte: https://geoserverdw.apps.geoapplications.net/geoserver/wfs/
"""

import os
import sys
import time
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent / "SHAPEFILES"
GEO = "https://geoserverdw.apps.geoapplications.net/geoserver/wfs/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Camadas essenciais para o Eureka Terra
LAYERS = [
    # (pasta, nome_layer, descricao)
    ("EMBARGOS", "workspace_sicar:vw_sicar_embargos", "Embargos (IBAMA+SEMAS+ICMBIO)"),
    ("TERRAS_INDIGENAS", "workspace_sicar:vw_sicar_terras_indigenas", "Terras Indigenas (FUNAI)"),
    ("UNIDADES_CONSERVACAO", "workspace_sicar:vw_sicar_unidades_conservacao", "Unidades de Conservacao (MMA/ICMBIO/IDEFLOR)"),
    ("QUILOMBOLAS", "workspace_sicar:vw_sicar_areas_quilombolas", "Areas Quilombolas (ITERPA+INCRA)"),
    ("ASSENTAMENTOS", "workspace_sicar:vw_sicar_assentamentos", "Assentamentos (INCRA+ITERPA)"),
    ("PRODES", "workspace_sicar:mv_desmatamento_prodes_2008", "Desmatamento PRODES 2008+ (INPE)"),
    ("PRODES_CERRADO", "workspace_sicar:mv_incremento_desmatamento_prodes_cerrado", "PRODES Cerrado (INPE)"),
    ("AUTOS_INFRACAO", "workspace_sicar:vw_sicar_autos_de_infracao", "Autos de Infracao (IBAMA+SEMAS)"),
    ("FLORESTAS_PUBLICAS", "workspace_sicar:vw_florestas_publicas_2024", "Florestas Publicas (SFB)"),
    ("ALERTAS_DETER", "workspace_fiscalizacao_inteligente:vw_alertas_deter", "Alertas DETER (INPE)"),
    ("CAR_ATIVO", "workspace_sicar:vw_car_ativo", "CARs Ativos (PA)"),
]

def baixar(pasta: str, layer: str, desc: str):
    caminho = BASE_DIR / pasta
    caminho.mkdir(parents=True, exist_ok=True)
    nome_arquivo = layer.replace(":", "_") + ".zip"
    destino = caminho / nome_arquivo

    if destino.exists():
        tamanho_kb = destino.stat().st_size / 1024
        print(f"  [OK] {nome_arquivo} ja existe ({tamanho_kb:.0f} KB)")
        return

    print(f"  Baixando: {desc}...")
    try:
        with httpx.stream("GET", GEO, params={
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": layer,
            "outputFormat": "SHAPE-ZIP",
        }, headers=HEADERS, timeout=600, verify=False) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(destino, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\r    {pct}% ({downloaded//1024}/{total//1024} KB)", end="")
            print(f"\r  [OK] {downloaded/1024:.0f} KB — {nome_arquivo}")
    except Exception as e:
        print(f"\r  [ERRO] {e}")
        if destino.exists():
            destino.unlink()


def main():
    print("=" * 60)
    print("DOWNLOAD SHAPEFILES — GeoServer Nacional Unificado")
    print(f"Fonte: {GEO}")
    print(f"Destino: {BASE_DIR}")
    print("=" * 60)

    for pasta, layer, desc in LAYERS:
        print(f"\n[{pasta}] {desc}")
        baixar(pasta, layer, desc)

    # Resumo
    print(f"\n{'=' * 60}")
    print("RESUMO")
    print(f"{'=' * 60}")
    total_kb = 0
    for pasta in sorted(BASE_DIR.iterdir()):
        if pasta.is_dir():
            arquivos = list(pasta.glob("*"))
            tam = sum(f.stat().st_size for f in arquivos)
            total_kb += tam / 1024
            print(f"  {pasta.name}: {len(arquivos)} arquivo(s), {tam/1024:.0f} KB")
    print(f"\n  TOTAL: {total_kb/1024:.1f} MB")
    print(f"\n[OK] Download concluido!")


if __name__ == "__main__":
    main()
