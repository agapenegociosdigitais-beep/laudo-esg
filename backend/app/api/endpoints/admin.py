"""Endpoints administrativos — listar usuários, gerenciar quotas e estatísticas."""
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminAtual, SessaoDB
from app.models.usuario import Usuario
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.schemas.admin import (
    AtualizarLimiteRequest,
    EstatisticasAdmin,
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
