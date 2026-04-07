"""
Endpoints para busca e listagem de propriedades rurais via SICAR.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import SessaoDB, UsuarioAtual
from app.models.propriedade import Propriedade
from app.schemas.propriedade import (
    BuscaCARRequest,
    CARResultado,
    PropriedadeLista,
    PropriedadeResposta,
)
from app.services.car_service import CARService

router = APIRouter()
car_service = CARService()


@router.post("/buscar-car", response_model=CARResultado)
async def buscar_por_car(dados: BuscaCARRequest, db: SessaoDB, usuario: UsuarioAtual):
    """
    Busca uma propriedade rural pelo n�mero do CAR no SICAR.

    Formato do CAR: UF-IBGE-IDENTIFICADOR
    Exemplo: MT-5107248-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    Retorna o `id` interno do banco para uso imediato no endpoint de an�lise.
    Se a propriedade j� estiver no banco (cache local), retorna instantaneamente.
    """
    numero_car = dados.numero_car.strip().upper()

    # ?Cache local: verifica se j� existe no banco ?
    resultado_db = await db.execute(
        select(Propriedade).where(Propriedade.numero_car == numero_car)
    )
    propriedade_local = resultado_db.scalar_one_or_none()

    if propriedade_local:
        return CARResultado(
            id=propriedade_local.id,
            numero_car=propriedade_local.numero_car,
            estado=propriedade_local.estado,
            municipio=propriedade_local.municipio,
            nome_propriedade=propriedade_local.nome_propriedade,
            area_ha=propriedade_local.area_ha,
            status_car=propriedade_local.status_car,
            bioma=propriedade_local.bioma,
            geojson=propriedade_local.geojson,
            fonte="SICAR (cache local)",
            encontrado=True,
        )

    # ?Consulta a API do SICAR ?
    resultado_sicar = await car_service.buscar_por_car(numero_car)

    if not resultado_sicar.encontrado:
        # SICAR indisponivel - continua com dados parciais
        resultado_sicar.numero_car = numero_car
        resultado_sicar.estado = numero_car.split("-")[0] if "-" in numero_car else "N/A"
        resultado_sicar.municipio = "Nao obtido"
        resultado_sicar.nome_propriedade = "Nome nao disponivel no SICAR"
        resultado_sicar.area_ha = 0.0
        resultado_sicar.status_car = "SICAR INDISPONIVEL"
        resultado_sicar.bioma = "Amazonia"
        resultado_sicar.geojson = None

    # ?Persiste no banco e retorna com o ID gerado ?
    nova_propriedade = Propriedade(
        numero_car=resultado_sicar.numero_car,
        estado=resultado_sicar.estado,
        municipio=resultado_sicar.municipio,
        nome_propriedade=resultado_sicar.nome_propriedade,
        area_ha=resultado_sicar.area_ha,
        status_car=resultado_sicar.status_car,
        bioma=resultado_sicar.bioma,
        geojson=resultado_sicar.geojson,
    )
    db.add(nova_propriedade)
    await db.flush()      # Gera o UUID antes do commit
    await db.refresh(nova_propriedade)

    # Retorna com o ID interno preenchido
    resultado_sicar.id = nova_propriedade.id
    return resultado_sicar


@router.get("/{propriedade_id}", response_model=PropriedadeResposta)
async def obter_propriedade(propriedade_id: uuid.UUID, db: SessaoDB, usuario: UsuarioAtual):
    """Retorna os dados completos de uma propriedade pelo ID interno."""
    resultado = await db.execute(
        select(Propriedade).where(Propriedade.id == propriedade_id)
    )
    propriedade = resultado.scalar_one_or_none()

    if not propriedade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade n�o encontrada.",
        )

    return PropriedadeResposta.model_validate(propriedade)


@router.get("/", response_model=PropriedadeLista)
async def listar_propriedades(
    db: SessaoDB,
    usuario: UsuarioAtual,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Lista todas as propriedades j� consultadas na plataforma (paginado)."""
    offset = (pagina - 1) * por_pagina

    # Contagem total eficiente
    total_resultado = await db.execute(select(func.count()).select_from(Propriedade))
    total = total_resultado.scalar_one()

    # P�gina de resultados
    resultado = await db.execute(
        select(Propriedade)
        .order_by(Propriedade.criado_em.desc())
        .offset(offset)
        .limit(por_pagina)
    )
    propriedades = resultado.scalars().all()

    return PropriedadeLista(
        total=total,
        pagina=pagina,
        itens=[PropriedadeResposta.model_validate(p) for p in propriedades],
    )
