#!/usr/bin/env python3
"""
Baixa shapefiles de todas as fontes governamentais para a pasta SHAPEFILES/.

Executar do diretório raiz do projeto:
  python scripts/download_shapefiles.py
"""

import os
import sys
import time
from pathlib import Path

import httpx

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(*args, **kwargs):
        return args[0] if args else kwargs.get("iterable", [])

BASE = Path(__file__).resolve().parent.parent / "SHAPEFILES"

HEADERS = {
    "User-Agent": "EurekaTerra/2.0 (geo-download; compliance@eurekaterra.com)",
}

FONTES = [
    {
        "pasta": "PRODES_INPE",
        "descricao": "PRODES Amazônia (INPE/TerraBrasilis)",
        "url": "https://terrabrasilis.dpi.inpe.br/geoserver/ows",
        "params": {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeName": "prodes-legal-amz:yearly_deforestation",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "prodes_amazonia.zip",
    },
    {
        "pasta": "PRODES_INPE",
        "descricao": "PRODES Cerrado (INPE/TerraBrasilis)",
        "url": "https://terrabrasilis.dpi.inpe.br/geoserver/ows",
        "params": {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeName": "prodes-cerrado-nb:yearly_deforestation",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "prodes_cerrado.zip",
    },
    {
        "pasta": "PRODES_INPE",
        "descricao": "PRODES Mata Atlântica (INPE/TerraBrasilis)",
        "url": "https://terrabrasilis.dpi.inpe.br/geoserver/ows",
        "params": {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeName": "prodes-mata-atlantica-nb:yearly_deforestation",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "prodes_mata_atlantica.zip",
    },
    {
        "pasta": "EMBARGOS_SEMAS_PA",
        "descricao": "Embargos SEMAS-PA (GeoServer LDI)",
        "url": "https://car.semas.pa.gov.br/geoserver/wfs",
        "params": {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeName": "ldi:ldi_areas_embargadas",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "embargos_semas_pa.zip",
    },
    {
        "pasta": "UNIDADES_CONSERVACAO_MMA",
        "descricao": "Unidades de Conservacao (CNUC/MMA)",
        "url": "https://cnuc.mma.gov.br/geoserver/wfs",
        "params": {
            "service": "WFS", "version": "1.1.0", "request": "GetFeature",
            "typeNames": "cnuc:unidades_conservacao",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "unidades_conservacao.zip",
        "offline": True,  # CNUC retorna HTML, nao WFS
    },
    {
        "pasta": "TERRAS_INDIGENAS_FUNAI",
        "descricao": "Terras Indigenas (FUNAI GeoServer)",
        "url": "https://geoserver.funai.gov.br/geoserver/Funai/wfs",
        "params": {
            "service": "WFS", "version": "1.1.0", "request": "GetFeature",
            "typeNames": "Funai:tis_poligonais",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "terras_indigenas.zip",
    },
    {
        "pasta": "QUILOMBOLAS_INCRA",
        "descricao": "Territorios Quilombolas (INCRA)",
        "url": "https://cmr.funai.gov.br/geoserver/wfs",
        "params": {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeName": "CMR-PUBLICO:lim_quilombolas_a",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "quilombolas.zip",
    },
    {
        "pasta": "ASSENTAMENTOS_INCRA",
        "descricao": "Assentamentos (INCRA)",
        "url": "https://cmr.funai.gov.br/geoserver/wfs",
        "params": {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeName": "CMR-PUBLICO:lim_assentamento_rural_a",
            "outputFormat": "SHAPE-ZIP",
        },
        "arquivo": "assentamentos.zip",
    },
]


def download_ibama():
    """IBAMA usa ArcGIS REST (não tem SHAPE-ZIP). Pagina e salva como GeoJSON."""
    pasta = BASE / "EMBARGOS_IBAMA"
    arquivo = pasta / "embargos_ibama.geojson"
    if arquivo.exists():
        print(f"  [OK] {arquivo.name} ja existe — pulando")
        return

    print(f"\n  Baixando Embargos IBAMA (paginação)...")
    base_url = (
        "https://pamgia.ibama.gov.br/server/rest/services/"
        "01_Publicacoes_Bases/adm_embargos_ibama_a/FeatureServer/0/query"
    )
    all_features = []
    offset = 0
    batch = 1000

    while True:
        resp = httpx.get(base_url, params={
            "where": "1=1",
            "outFields": "num_tad,seq_tad,uf,municipio,qtd_area_embargada,dat_embargo,des_infracao,nome_embargado,cpf_cnpj_embargado",
            "returnGeometry": "true",
            "f": "geojson",
            "resultOffset": str(offset),
            "resultRecordCount": str(batch),
        }, headers=HEADERS, timeout=120, verify=False)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        print(f"    offset={offset}: {len(features)} registros (total={len(all_features)})")
        offset += batch
        if len(features) < batch:
            break

    import json
    geojson = {"type": "FeatureCollection", "features": all_features}
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    print(f"  [OK] {len(all_features)} registros salvos em {arquivo.name}")


def baixar_arquivo(fonte: dict):
    pasta = BASE / fonte["pasta"]
    caminho = pasta / fonte["arquivo"]

    if fonte.get("offline"):
        print(f"  [OFFLINE] {fonte['descricao']} — servidor indisponivel, pulando")
        return

    if caminho.exists():
        print(f"  [OK] {fonte['arquivo']} ja existe ({caminho.stat().st_size / 1024:.0f} KB) — pulando")
        return

    print(f"  Baixando: {fonte['descricao']}...")
    try:
        with httpx.stream("GET", fonte["url"], params=fonte["params"],
                          headers=HEADERS, timeout=300, verify=False) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            with open(caminho, "wb") as f:
                if total:
                    with tqdm(total=total, unit="B", unit_scale=True, desc=f"    {fonte['arquivo']}") as pbar:
                        for chunk in resp.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:
                    for chunk in resp.iter_bytes(chunk_size=8192):
                        f.write(chunk)
        tamanho = caminho.stat().st_size
        print(f"  [OK] {tamanho / 1024:.0f} KB — {fonte['arquivo']}")
    except Exception as e:
        print(f"  [ERRO] {e}")
        if caminho.exists():
            caminho.unlink()


def main():
    print("=" * 60)
    print("DOWNLOAD DE SHAPEFILES — Eureka Terra")
    print(f"Destino: {BASE}")
    print("=" * 60)

    for fonte in FONTES:
        print(f"\n[{fonte['pasta']}]")
        baixar_arquivo(fonte)

    print(f"\n[EMBARGOS_IBAMA]")
    download_ibama()

    # Resumo
    print(f"\n{'=' * 60}")
    print("RESUMO")
    print(f"{'=' * 60}")
    for pasta in sorted(BASE.iterdir()):
        if pasta.is_dir():
            arquivos = list(pasta.glob("*"))
            tamanho = sum(f.stat().st_size for f in arquivos)
            print(f"  {pasta.name}: {len(arquivos)} arquivo(s), {tamanho / 1024:.0f} KB")
    print(f"\n[OK] Download concluido!")


if __name__ == "__main__":
    main()
