"""Endpoints administrativos — listar usuários, gerenciar quotas e estatísticas."""
import logging
import time
from datetime import datetime
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminAtual, SessaoDB
from app.models.usuario import Usuario
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.schemas.admin import (
    AnaliseAdminResposta,
    AtualizarLimiteRequest,
    EstatisticasAdmin,
    StatusAPI,
    StatusAPIsExternas,
    TopUsuario,
    UsuarioAdminResposta,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/usuarios", response_model=list[UsuarioAdminResposta])
async def listar_usuarios(
    db: SessaoDB,
    admin: AdminAtual,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Lista todos os usuários com informações de quota."""
    offset = (pagina - 1) * por_pagina
    resultado = await db.execute(
        select(Usuario)
        .order_by(Usuario.criado_em.desc())
        .offset(offset)
        .limit(por_pagina)
    )
    usuarios = resultado.scalars().all()
    return [UsuarioAdminResposta.model_validate(u) for u in usuarios]


@router.patch("/usuarios/{usuario_id}/ativar")
async def ativar_usuario(
    usuario_id: str,
    db: SessaoDB,
    admin: AdminAtual,
):
    """Ativa um usuário desativado."""
    usuario = await db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    usuario.ativo = True
    await db.flush()
    await db.commit()
    return {"mensagem": "Usuário ativado.", "usuario_id": usuario_id}


@router.patch("/usuarios/{usuario_id}/desativar")
async def desativar_usuario(
    usuario_id: str,
    db: SessaoDB,
    admin: AdminAtual,
):
    """Desativa um usuário (bloqueia acesso)."""
    usuario = await db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    usuario.ativo = False
    await db.flush()
    await db.commit()
    return {"mensagem": "Usuário desativado.", "usuario_id": usuario_id}


@router.patch("/usuarios/{usuario_id}/limite")
async def atualizar_limite_consultas(
    usuario_id: str,
    dados: AtualizarLimiteRequest,
    db: SessaoDB,
    admin: AdminAtual,
):
    """Atualiza limite de consultas mensais (NULL = sem limite)."""
    usuario = await db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    usuario.limite_consultas = dados.limite_consultas
    await db.flush()
    await db.commit()
    return {
        "mensagem": "Limite atualizado.",
        "usuario_id": usuario_id,
        "novo_limite": dados.limite_consultas,
    }


@router.get("/estatisticas", response_model=EstatisticasAdmin)
async def obter_estatisticas(
    db: SessaoDB,
    admin: AdminAtual,
):
    """Retorna estatísticas gerais da plataforma."""
    # Total de usuários
    res_total = await db.execute(select(func.count()).select_from(Usuario))
    total_usuarios = res_total.scalar() or 0

    # Usuários ativos
    res_ativos = await db.execute(
        select(func.count()).select_from(Usuario).where(Usuario.ativo == True)
    )
    usuarios_ativos = res_ativos.scalar() or 0

    # Total de análises
    res_analises = await db.execute(select(func.count()).select_from(Analise))
    total_analises = res_analises.scalar() or 0

    # Análises do mês atual
    mes_atual = datetime.now().strftime("%Y-%m")
    res_mes = await db.execute(
        select(func.count())
        .select_from(Analise)
        .where(func.to_char(Analise.criado_em, "YYYY-MM") == mes_atual)
    )
    analises_mes_atual = res_mes.scalar() or 0

    # CARs consultados (distintos)
    res_cars = await db.execute(
        select(func.count(func.distinct(Propriedade.numero_car))).select_from(Propriedade)
    )
    cars_consultados = res_cars.scalar() or 0

    # Top 5 usuários por consultas_mes_atual
    res_top = await db.execute(
        select(Usuario.nome, Usuario.email, Usuario.consultas_mes_atual)
        .order_by(Usuario.consultas_mes_atual.desc())
        .limit(5)
    )
    top_usuarios = [
        TopUsuario(nome=row[0], email=row[1], consultas_mes=row[2] or 0)
        for row in res_top.fetchall()
    ]

    return EstatisticasAdmin(
        total_usuarios=total_usuarios,
        usuarios_ativos=usuarios_ativos,
        total_analises=total_analises,
        analises_mes_atual=analises_mes_atual,
        cars_consultados=cars_consultados,
        top_usuarios=top_usuarios,
    )


@router.get("/analises", response_model=list[AnaliseAdminResposta])
async def listar_analises_admin(
    db: SessaoDB,
    admin: AdminAtual,
    status: Annotated[Optional[str], Query()] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Lista todas as análises com filtro por status."""
    offset = (pagina - 1) * por_pagina

    query = select(
        Analise.id,
        Propriedade.numero_car,
        Propriedade.nome_propriedade,
        Usuario.email,
        Analise.status,
        Analise.score_esg,
        Analise.nivel_risco,
        Analise.criado_em,
    ).join(
        Propriedade, Analise.propriedade_id == Propriedade.id
    ).outerjoin(
        Usuario, Analise.usuario_id == Usuario.id
    )

    if status:
        query = query.where(Analise.status == status)

    query = query.order_by(Analise.criado_em.desc()).offset(offset).limit(por_pagina)

    resultado = await db.execute(query)
    linhas = resultado.fetchall()

    return [
        AnaliseAdminResposta(
            id=row[0],
            numero_car=row[1],
            nome_propriedade=row[2],
            usuario_email=row[3],
            status=row[4],
            score_esg=row[5],
            nivel_risco=row[6],
            criado_em=row[7],
        )
        for row in linhas
    ]


async def _verificar_api(url: str, timeout: int = 5) -> tuple[bool, Optional[int]]:
    """Verifica se uma API está online e retorna latência em ms."""
    try:
        inicio = time.time()
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            resp = await client.head(url, follow_redirects=True)
            latencia_ms = int((time.time() - inicio) * 1000)
            online = 200 <= resp.status_code < 500
            return online, latencia_ms if online else None
    except Exception as e:
        logger.warning(f"Erro ao verificar API {url}: {e}")
        return False, None


@router.get("/apis/status", response_model=StatusAPIsExternas)
async def verificar_status_apis(admin: AdminAtual):
    """Verifica status das APIs externas (IBAMA, SEMAS, PRODES)."""
    ibama_online, ibama_latencia = await _verificar_api(
        "https://pamgia.ibama.gov.br/server/rest/services/01_Publicacoes_Bases/adm_embargos_ibama_a/FeatureServer/0/query?where=1=1&resultRecordCount=1&f=json"
    )

    semas_online, semas_latencia = await _verificar_api(
        "https://monitoramento.semas.pa.gov.br/ldi/"
    )

    prodes_online, prodes_latencia = await _verificar_api(
        "https://terrabrasilis.dpi.inpe.br/geoserver/ows?service=WFS&version=2.0.0&request=GetCapabilities"
    )

    agora = datetime.utcnow()

    return StatusAPIsExternas(
        ibama=StatusAPI(online=ibama_online, latencia_ms=ibama_latencia, ultima_verificacao=agora),
        semas=StatusAPI(online=semas_online, latencia_ms=semas_latencia, ultima_verificacao=agora),
        prodes=StatusAPI(online=prodes_online, latencia_ms=prodes_latencia, ultima_verificacao=agora),
    )
