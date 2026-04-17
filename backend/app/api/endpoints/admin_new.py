"""Endpoints para painel administrativo — Versão 2.0 Completa."""
import logging
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.admin_security import obter_admin_atual
from app.models.admin import AdminUser, AdminNotification
from app.models.usuario import Usuario
from app.schemas.admin import (
    AdminLoginRequest, AdminTokenResposta, AdminResposta,
    ClientePerfil, ClienteListaItem, AprovarClienteRequest, EditarLimiteRequest,
    NotificacaoResposta, AdminActionResposta, OverviewMetricas,
    DashboardGraficos,
)
from app.services.admin_service import AdminService
from app.core.admin_security import admin_jwt
from app.core.security import gerar_hash_senha, verificar_senha

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

SessaoDB = Annotated[AsyncSession, Depends(get_db)]
AdminAtual = Annotated[AdminUser, Depends(obter_admin_atual)]


# ─────────────────────────────────────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AdminTokenResposta)
async def admin_login(
    credenciais: AdminLoginRequest,
    db: SessaoDB
):
    """Login do administrador com email e senha.

    Credenciais devem corresponder ao ADMIN_EMAIL e ADMIN_PASSWORD do .env
    """
    from app.core.config import get_settings
    settings = get_settings()

    # Validar email
    if credenciais.email != settings.ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    # Validar senha
    if not verificar_senha(credenciais.password, settings.ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    # Buscar ou criar admin no banco
    from sqlalchemy import select
    stmt = select(AdminUser).where(AdminUser.email == credenciais.email)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        # Criar admin na primeira vez
        admin = AdminUser(
            email=credenciais.email,
            password_hash=settings.ADMIN_PASSWORD_HASH,
            role="super_admin"
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

    # Gerar token
    token = admin_jwt.criar_token(str(admin.id))

    # Registrar login
    await AdminService.registrar_login(db, admin.id)

    return AdminTokenResposta(
        access_token=token,
        token_type="Bearer",
        admin=AdminResposta.model_validate(admin)
    )


@router.post("/logout")
async def admin_logout(admin: AdminAtual):
    """Logout do administrador."""
    # Token é invalidado no frontend (Cookies/Storage)
    return {"message": "Logout realizado com sucesso"}


@router.get("/me", response_model=AdminResposta)
async def admin_perfil(admin: AdminAtual):
    """Retorna informações do administrador autenticado."""
    return AdminResposta.model_validate(admin)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD — MÉTRICAS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/metrics/overview", response_model=OverviewMetricas)
async def metricas_overview(
    db: SessaoDB,
    admin: AdminAtual
):
    """Obtém métricas de visão geral para o dashboard."""
    return await AdminService.get_overview_metricas(db)


@router.get("/metrics/graficos", response_model=DashboardGraficos)
async def dashboard_graficos(
    db: SessaoDB,
    admin: AdminAtual
):
    """Obtém dados para todos os gráficos do dashboard."""
    return await AdminService.get_dashboard_graficos(db)


# ─────────────────────────────────────────────────────────────────────────────
# GESTÃO DE CLIENTES
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/clientes", response_model=dict)
async def listar_clientes(
    db: SessaoDB,
    admin: AdminAtual,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    """Lista clientes com paginação, filtros e busca."""
    usuarios, total = await AdminService.listar_clientes_paginado(
        db, page, page_size, status, search
    )

    # Registrar visualização no log
    await AdminService.registrar_acao(db, admin.id, "view_clients_list", "system")

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": [ClienteListaItem.model_validate(u) for u in usuarios]
    }


@router.get("/clientes/{cliente_id}", response_model=ClientePerfil)
async def get_cliente_perfil(
    cliente_id: UUID,
    db: SessaoDB,
    admin: AdminAtual,
):
    """Obtém perfil detalhado de um cliente."""
    cliente = await AdminService.get_cliente_perfil(db, cliente_id)

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )

    await AdminService.registrar_acao(
        db, admin.id, "view_client_profile", "client", cliente_id
    )

    return ClientePerfil.model_validate(cliente)


@router.patch("/clientes/{cliente_id}/aprovar", response_model=ClientePerfil)
async def aprovar_cliente(
    cliente_id: UUID,
    db: SessaoDB,
    admin: AdminAtual,
    request: AprovarClienteRequest,
):
    """Aprova um cliente, liberando acesso ao sistema."""
    try:
        cliente = await AdminService.aprovar_cliente(db, admin.id, cliente_id)
        return ClientePerfil.model_validate(cliente)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/clientes/{cliente_id}/desaprovar", response_model=ClientePerfil)
async def desaprovar_cliente(
    cliente_id: UUID,
    db: SessaoDB,
    admin: AdminAtual,
):
    """Desaprova um cliente, bloqueando seu acesso."""
    try:
        cliente = await AdminService.desaprovar_cliente(db, admin.id, cliente_id)
        return ClientePerfil.model_validate(cliente)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/clientes/{cliente_id}/suspender", response_model=ClientePerfil)
async def suspender_cliente(
    cliente_id: UUID,
    db: SessaoDB,
    admin: AdminAtual,
):
    """Suspende temporariamente um cliente."""
    try:
        cliente = await AdminService.suspender_cliente(db, admin.id, cliente_id)
        return ClientePerfil.model_validate(cliente)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/clientes/{cliente_id}/limite", response_model=ClientePerfil)
async def editar_limite_cliente(
    cliente_id: UUID,
    db: SessaoDB,
    admin: AdminAtual,
    request: EditarLimiteRequest,
):
    """Edita o limite mensal de pesquisas de um cliente."""
    try:
        cliente = await AdminService.editar_limite(
            db, admin.id, cliente_id, request.novo_limite
        )
        return ClientePerfil.model_validate(cliente)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/notificacoes", response_model=dict)
async def listar_notificacoes(
    db: SessaoDB,
    admin: AdminAtual,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    apenas_nao_lidas: bool = False,
):
    """Lista notificações com paginação."""
    notifs, total = await AdminService.listar_notificacoes(
        db, page, page_size, apenas_nao_lidas
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": [NotificacaoResposta.model_validate(n) for n in notifs]
    }


@router.get("/notificacoes/unread-count", response_model=dict)
async def contar_notificacoes_nao_lidas(
    db: SessaoDB,
    admin: AdminAtual,
):
    """Contagem de notificações não lidas."""
    count = await AdminService.contar_notificacoes_nao_lidas(db)
    return {"unread_count": count}


@router.patch("/notificacoes/{notif_id}/ler", response_model=NotificacaoResposta)
async def marcar_notificacao_lida(
    notif_id: UUID,
    db: SessaoDB,
    admin: AdminAtual,
):
    """Marca uma notificação como lida."""
    notif = await AdminService.marcar_notificacao_lida(db, notif_id)

    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada"
        )

    return NotificacaoResposta.model_validate(notif)


# ─────────────────────────────────────────────────────────────────────────────
# AUDITORIA
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/logs", response_model=dict)
async def listar_logs_auditoria(
    db: SessaoDB,
    admin: AdminAtual,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    action_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Lista log de auditoria com filtros opcionais."""
    from sqlalchemy import select, func, and_
    from app.models.admin import AdminActionLog

    query = select(AdminActionLog)

    if action_type:
        query = query.where(AdminActionLog.action_type == action_type)

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.where(AdminActionLog.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.where(AdminActionLog.created_at <= dt_to)
        except ValueError:
            pass

    # Contar total
    count_stmt = select(func.count(AdminActionLog.id))
    if action_type:
        count_stmt = count_stmt.where(AdminActionLog.action_type == action_type)
    total = await db.scalar(count_stmt) or 0

    # Paginação
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(AdminActionLog.created_at.desc())

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": [AdminActionResposta.model_validate(log) for log in logs]
    }


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/config/password")
async def alterar_senha_admin(
    db: SessaoDB,
    admin: AdminAtual,
    senha_atual: str,
    senha_nova: str,
):
    """Altera a senha do administrador."""
    from app.core.config import get_settings
    from app.core.security import gerar_hash_senha, verificar_senha

    settings = get_settings()

    # Verificar senha atual
    if not verificar_senha(senha_atual, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta"
        )

    # Atualizar hash
    novo_hash = gerar_hash_senha(senha_nova)
    admin.password_hash = novo_hash
    db.add(admin)

    # Registrar ação
    await AdminService.registrar_acao(db, admin.id, "change_password", "system")

    await db.commit()

    return {"message": "Senha alterada com sucesso"}


@router.get("/config/info")
async def info_sistema(
    db: SessaoDB,
    admin: AdminAtual,
):
    """Retorna informações do sistema."""
    from app.core.config import get_settings
    from sqlalchemy import text

    settings = get_settings()

    # Contar registros
    from app.models.usuario import Usuario
    from app.models.propriedade import Propriedade
    from app.models.analise import Analise
    from sqlalchemy import select, func

    total_usuarios = await db.scalar(select(func.count(Usuario.id))) or 0
    total_propriedades = await db.scalar(select(func.count(Propriedade.id))) or 0
    total_analises = await db.scalar(select(func.count(Analise.id))) or 0

    return {
        "versao": "2.0.0",
        "ambiente": settings.ENVIRONMENT,
        "total_usuarios": total_usuarios,
        "total_propriedades": total_propriedades,
        "total_analises": total_analises,
        "banco_dados": "PostgreSQL com PostGIS",
    }
