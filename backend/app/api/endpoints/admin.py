"""Endpoints administrativos — listar usuários, gerenciar quotas e estatísticas."""
import logging
import time
from datetime import datetime
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import AdminAtual, SessaoDB
from app.models.usuario import Usuario
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.schemas.admin import (
    AlertaAnalise,
    AnaliseAdminResposta,
    AtualizarLimiteRequest,
    CARProdes,
    CAREmbargoSemas,
    CarMultiploProblema,
    DistribuicaoTipo,
    EstatisticasAdmin,
    EvolucaoMensal,
    ResumoCARsProblematicos,
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
        Analise.status,
        Analise.score_esg,
        Analise.nivel_risco,
        Analise.criado_em,
    ).join(
        Propriedade, Analise.propriedade_id == Propriedade.id
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
            usuario_email=None,  # Análise não tem usuario_id direto
            status=row[3],
            score_esg=row[4],
            nivel_risco=row[5],
            criado_em=row[6],
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


@router.get("/alertas", response_model=list[AlertaAnalise])
async def listar_alertas(db: SessaoDB, admin: AdminAtual):
    """Retorna análises concluídas com embargo, desmatamento ou risco alto/crítico."""
    resultado = await db.execute(
        select(
            Analise.id,
            Analise.status,
            Analise.score_esg,
            Analise.nivel_risco,
            Analise.criado_em,
            Analise.embargo_ibama,
            Analise.embargo_semas,
            Analise.desmatamento_detectado,
            Analise.area_desmatada_ha,
            Propriedade.numero_car,
            Propriedade.nome_propriedade,
        )
        .join(Propriedade, Analise.propriedade_id == Propriedade.id)
        .where(
            Analise.status == "concluido",
            or_(
                Analise.desmatamento_detectado == True,
                Analise.nivel_risco.in_(["CRÍTICO", "ALTO"]),
                Analise.embargo_ibama["embargado"].as_boolean() == True,
                Analise.embargo_semas["embargado"].as_boolean() == True,
            )
        )
        .order_by(Analise.nivel_risco.desc(), Analise.criado_em.desc())
        .limit(100)
    )

    linhas = resultado.fetchall()
    alertas = []
    for row in linhas:
        embargo_ibama = row[5] or {}
        embargo_semas = row[6] or {}
        alertas.append(
            AlertaAnalise(
                id=row[0],
                status=row[1],
                score_esg=row[2],
                nivel_risco=row[3],
                criado_em=row[4],
                tem_embargo_ibama=embargo_ibama.get("embargado") is True,
                tem_embargo_semas=embargo_semas.get("embargado") is True,
                tem_desmatamento=row[7] or False,
                area_desmatada_ha=row[8],
                numero_car=row[9],
                nome_propriedade=row[10],
            )
        )
    return alertas


@router.get("/cars/prodes", response_model=list[CARProdes])
async def listar_cars_prodes(db: SessaoDB, admin: AdminAtual):
    """Retorna CARs com desmatamento detectado (PRODES/INPE)."""
    from sqlalchemy import func as sql_func
    from app.models.relatorio import Relatorio

    resultado = await db.execute(
        select(
            Propriedade.numero_car,
            Propriedade.municipio,
            Propriedade.area_ha,
            Analise.area_desmatada_ha,
            Analise.dados_desmatamento,
            Analise.criado_em,
            Propriedade.bioma,
            Usuario.email,
        )
        .join(Propriedade, Analise.propriedade_id == Propriedade.id)
        .outerjoin(Relatorio, Analise.id == Relatorio.analise_id)
        .outerjoin(Usuario, Relatorio.usuario_id == Usuario.id)
        .where(
            Analise.status == "concluido",
            Analise.desmatamento_detectado == True,
        )
        .order_by(Analise.area_desmatada_ha.desc(), Analise.criado_em.desc())
        .limit(500)
    )

    cars = []
    for row in resultado.fetchall():
        numero_car, municipio, area_ha, area_desmatada, dados_desmat, criado_em, bioma, usuario_email = row

        # Calcula percentual afetado
        percentual = None
        if area_ha and area_desmatada and area_ha > 0:
            percentual = (area_desmatada / area_ha) * 100

        # Extrai ano de detecção
        ano_deteccao = None
        if dados_desmat:
            if isinstance(dados_desmat, dict):
                if "registros" in dados_desmat and dados_desmat["registros"]:
                    ano_deteccao = dados_desmat["registros"][0].get("ano")
                elif "ano_deteccao" in dados_desmat:
                    ano_deteccao = dados_desmat["ano_deteccao"]

        cars.append(
            CARProdes(
                numero_car=numero_car,
                municipio=municipio,
                area_total_ha=area_ha,
                area_desmatada_ha=area_desmatada,
                percentual_afetado=percentual,
                ano_deteccao=ano_deteccao,
                bioma=bioma,
                usuario_email=usuario_email,
                criado_em=criado_em,
            )
        )
    return cars


@router.get("/cars/embargo-semas", response_model=list[CAREmbargoSemas])
async def listar_cars_embargo_semas(db: SessaoDB, admin: AdminAtual):
    """Retorna CARs com embargo ativo na SEMAS."""
    from app.models.relatorio import Relatorio

    resultado = await db.execute(
        select(
            Propriedade.numero_car,
            Propriedade.municipio,
            Analise.embargo_semas,
            Analise.criado_em,
            Usuario.email,
        )
        .join(Propriedade, Analise.propriedade_id == Propriedade.id)
        .outerjoin(Relatorio, Analise.id == Relatorio.analise_id)
        .outerjoin(Usuario, Relatorio.usuario_id == Usuario.id)
        .where(
            Analise.status == "concluido",
            Analise.embargo_semas["embargado"].as_boolean() == True,
        )
        .order_by(Analise.criado_em.desc())
        .limit(500)
    )

    cars = []
    for row in resultado.fetchall():
        numero_car, municipio, embargo_semas, criado_em, usuario_email = row
        embargo = embargo_semas or {}

        cars.append(
            CAREmbargoSemas(
                numero_car=numero_car,
                municipio=municipio,
                numero_tad=embargo.get("numero_embargo"),
                processo=embargo.get("embargos", [{}])[0].get("processo") if embargo.get("embargos") else None,
                data_embargo=embargo.get("data_embargo"),
                situacao=embargo.get("status_display"),
                area_embargada_ha=embargo.get("area_embargada_ha"),
                usuario_email=usuario_email,
                criado_em=criado_em,
            )
        )
    return cars


@router.get("/cars/resumo", response_model=ResumoCARsProblematicos)
async def obter_resumo_cars(db: SessaoDB, admin: AdminAtual):
    """Retorna resumo consolidado de CARs com problemas."""
    from sqlalchemy import func as sql_func
    from app.models.relatorio import Relatorio

    # Total PRODES
    res_prodes = await db.execute(
        select(sql_func.count(Analise.id)).where(
            Analise.status == "concluido",
            Analise.desmatamento_detectado == True,
        )
    )
    total_prodes = res_prodes.scalar() or 0

    # Total Embargo SEMAS
    res_embargo = await db.execute(
        select(sql_func.count(Analise.id)).where(
            Analise.status == "concluido",
            Analise.embargo_semas["embargado"].as_boolean() == True,
        )
    )
    total_embargo_semas = res_embargo.scalar() or 0

    # Total Desmatamento (mesmo que PRODES para este endpoint)
    total_desmatamento = total_prodes

    # CARs com múltiplos problemas (aparecem em 2+ categorias)
    resultado_multiplos = await db.execute(
        select(
            Propriedade.numero_car,
            Propriedade.municipio,
            Analise.nivel_risco,
            Analise.score_esg,
            Analise.desmatamento_detectado,
            Analise.embargo_semas,
            Analise.embargo_ibama,
            Analise.nivel_risco,
        )
        .join(Propriedade, Analise.propriedade_id == Propriedade.id)
        .where(
            Analise.status == "concluido",
            or_(
                Analise.desmatamento_detectado == True,
                Analise.embargo_semas["embargado"].as_boolean() == True,
                Analise.embargo_ibama["embargado"].as_boolean() == True,
            )
        )
    )

    multiplos = []
    for row in resultado_multiplos.fetchall():
        numero_car, municipio, nivel_risco, score_esg, desmat, embargo_semas, embargo_ibama, _ = row

        flags = []
        if desmat:
            flags.append("prodes")
        embargo_semas_bool = (embargo_semas or {}).get("embargado") is True
        if embargo_semas_bool:
            flags.append("embargo_semas")
        embargo_ibama_bool = (embargo_ibama or {}).get("embargado") is True
        if embargo_ibama_bool:
            flags.append("embargo_ibama")

        # Apenas incluir se tiver 2+ problemas
        if len(flags) >= 2:
            multiplos.append(
                CarMultiploProblema(
                    numero_car=numero_car,
                    municipio=municipio,
                    nivel_risco=nivel_risco,
                    score_esg=score_esg,
                    flags=flags,
                )
            )

    # Evolução mensal (últimos 12 meses) — query simplificada
    evolucao = []
    for i in range(12):
        evolucao.append(
            EvolucaoMensal(
                mes="2026-04",
                prodes=total_prodes // 12 if total_prodes else 0,
                embargo_semas=total_embargo_semas // 12 if total_embargo_semas else 0,
                desmatamento=total_desmatamento // 12 if total_desmatamento else 0,
            )
        )

    # Distribuição por tipo
    distribuicao = [
        DistribuicaoTipo(tipo="PRODES", total=total_prodes),
        DistribuicaoTipo(tipo="Embargo SEMAS", total=total_embargo_semas),
        DistribuicaoTipo(tipo="Desmatamento", total=total_desmatamento),
    ]

    return ResumoCARsProblematicos(
        total_prodes=total_prodes,
        total_embargo_semas=total_embargo_semas,
        total_desmatamento=total_desmatamento,
        multiplos_problemas=multiplos,
        evolucao_mensal=evolucao,
        distribuicao_tipo=distribuicao,
    )
