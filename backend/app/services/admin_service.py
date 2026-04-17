"""Serviço de lógica de negócio para painel administrativo."""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario
from app.models.admin import AdminUser, SearchLog, FlaggedCar, AdminActionLog, AdminNotification
from app.models.analise import Analise
from app.schemas.admin import (
    OverviewMetricas, PesquisasPorDia, CARsPorStatus, TopCliente, DashboardGraficos
)

logger = logging.getLogger(__name__)


class AdminService:
    """Serviço para operações administrativas."""

    # ─────────────────────────────────────────────────────────────────────────
    # AUTENTICAÇÃO E SEGURANÇA
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def registrar_login(db: AsyncSession, admin_id: UUID) -> None:
        """Registra o login do administrador."""
        stmt = select(AdminUser).where(AdminUser.id == admin_id)
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin:
            admin.last_login = datetime.utcnow()
            db.add(admin)
            await db.commit()

    @staticmethod
    async def registrar_acao(
        db: AsyncSession,
        admin_id: UUID,
        action_type: str,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        details: Optional[dict] = None
    ) -> AdminActionLog:
        """Registra uma ação do administrador no log imutável."""
        acao = AdminActionLog(
            admin_id=admin_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            details=details or {}
        )
        db.add(acao)
        await db.commit()
        return acao

    # ─────────────────────────────────────────────────────────────────────────
    # GESTÃO DE CLIENTES
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def listar_clientes_paginado(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Usuario], int]:
        """Lista clientes com paginação e filtros.

        Args:
            db: Sessão do banco
            page: Página (começa em 1)
            page_size: Registros por página
            status_filter: Filtro de status (ativo|inativo|pendente|suspenso)
            search: Busca por nome ou email

        Returns:
            Tupla (lista de usuários, total de registros)
        """
        query = select(Usuario)

        # Aplicar filtros
        if status_filter == "ativo":
            query = query.where(Usuario.ativo == True)
        elif status_filter == "inativo":
            query = query.where(Usuario.ativo == False)
        elif status_filter == "pendente":
            query = query.where(Usuario.requerente_aprovacao == True)
        elif status_filter == "suspenso":
            query = query.where(Usuario.suspended_at != None)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Usuario.nome.ilike(search_term),
                    Usuario.email.ilike(search_term)
                )
            )

        # Contar total
        count_stmt = select(func.count()).select_from(Usuario).distinct()
        if status_filter or search:
            # Aplicar mesmos filtros na contagem
            if status_filter == "ativo":
                count_stmt = count_stmt.where(Usuario.ativo == True)
            elif status_filter == "inativo":
                count_stmt = count_stmt.where(Usuario.ativo == False)
            elif status_filter == "pendente":
                count_stmt = count_stmt.where(Usuario.requerente_aprovacao == True)
            elif status_filter == "suspenso":
                count_stmt = count_stmt.where(Usuario.suspended_at != None)

            if search:
                search_term = f"%{search}%"
                count_stmt = count_stmt.where(
                    or_(
                        Usuario.nome.ilike(search_term),
                        Usuario.email.ilike(search_term)
                    )
                )

        total = await db.scalar(count_stmt)

        # Paginação
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Usuario.criado_em.desc())

        result = await db.execute(query)
        usuarios = result.scalars().all()

        return usuarios, total

    @staticmethod
    async def get_cliente_perfil(db: AsyncSession, cliente_id: UUID) -> Optional[Usuario]:
        """Obtém perfil completo de um cliente."""
        stmt = select(Usuario).where(Usuario.id == cliente_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def aprovar_cliente(db: AsyncSession, admin_id: UUID, cliente_id: UUID) -> Usuario:
        """Aprova um cliente, liberando acesso completo."""
        stmt = select(Usuario).where(Usuario.id == cliente_id)
        result = await db.execute(stmt)
        cliente = result.scalar_one_or_none()

        if not cliente:
            raise ValueError(f"Cliente {cliente_id} não encontrado")

        cliente.ativo = True
        cliente.requerente_aprovacao = False
        cliente.approved_at = datetime.utcnow()
        db.add(cliente)

        # Log de auditoria
        await AdminService.registrar_acao(
            db, admin_id, "approve_client", "client", cliente_id,
            {"cliente_email": cliente.email, "cliente_nome": cliente.nome}
        )

        # Criar notificação
        await AdminService.criar_notificacao(
            db, "client_approved", f"Cliente {cliente.nome} aprovado",
            f"{cliente.email} agora tem acesso ao sistema", cliente_id
        )

        await db.commit()
        return cliente

    @staticmethod
    async def desaprovar_cliente(db: AsyncSession, admin_id: UUID, cliente_id: UUID) -> Usuario:
        """Desaprova um cliente, bloqueando seu acesso."""
        stmt = select(Usuario).where(Usuario.id == cliente_id)
        result = await db.execute(stmt)
        cliente = result.scalar_one_or_none()

        if not cliente:
            raise ValueError(f"Cliente {cliente_id} não encontrado")

        cliente.ativo = False
        cliente.requerente_aprovacao = True
        db.add(cliente)

        # Log de auditoria
        await AdminService.registrar_acao(
            db, admin_id, "disapprove_client", "client", cliente_id,
            {"cliente_email": cliente.email, "cliente_nome": cliente.nome}
        )

        await db.commit()
        return cliente

    @staticmethod
    async def suspender_cliente(db: AsyncSession, admin_id: UUID, cliente_id: UUID) -> Usuario:
        """Suspende temporariamente um cliente."""
        stmt = select(Usuario).where(Usuario.id == cliente_id)
        result = await db.execute(stmt)
        cliente = result.scalar_one_or_none()

        if not cliente:
            raise ValueError(f"Cliente {cliente_id} não encontrado")

        cliente.ativo = False
        cliente.suspended_at = datetime.utcnow()
        db.add(cliente)

        # Log de auditoria
        await AdminService.registrar_acao(
            db, admin_id, "suspend_client", "client", cliente_id,
            {"cliente_email": cliente.email}
        )

        await db.commit()
        return cliente

    @staticmethod
    async def editar_limite(
        db: AsyncSession,
        admin_id: UUID,
        cliente_id: UUID,
        novo_limite: Optional[int]
    ) -> Usuario:
        """Edita o limite mensal de pesquisas de um cliente."""
        stmt = select(Usuario).where(Usuario.id == cliente_id)
        result = await db.execute(stmt)
        cliente = result.scalar_one_or_none()

        if not cliente:
            raise ValueError(f"Cliente {cliente_id} não encontrado")

        limite_anterior = cliente.limite_consultas
        cliente.limite_consultas = novo_limite
        db.add(cliente)

        # Log de auditoria
        await AdminService.registrar_acao(
            db, admin_id, "edit_limit", "client", cliente_id,
            {"cliente_email": cliente.email, "limite_anterior": limite_anterior, "novo_limite": novo_limite}
        )

        await db.commit()
        return cliente

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTRICAS E DASHBOARD
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_overview_metricas(db: AsyncSession) -> OverviewMetricas:
        """Obtém métricas de visão geral para o dashboard."""

        # Total de clientes por status
        total_clientes = await db.scalar(select(func.count(Usuario.id)))
        clientes_ativos = await db.scalar(
            select(func.count(Usuario.id)).where(Usuario.ativo == True)
        )
        clientes_inativos = await db.scalar(
            select(func.count(Usuario.id)).where(Usuario.ativo == False)
        )
        clientes_pendentes = await db.scalar(
            select(func.count(Usuario.id)).where(Usuario.requerente_aprovacao == True)
        )

        # Pesquisas
        agora = datetime.utcnow()
        hoje = agora.date()
        semana_atras = agora - timedelta(days=7)
        mes_atras = agora - timedelta(days=30)

        total_pesquisas_hoje = await db.scalar(
            select(func.count(SearchLog.id)).where(func.date(SearchLog.searched_at) == hoje)
        )
        total_pesquisas_semana = await db.scalar(
            select(func.count(SearchLog.id)).where(SearchLog.searched_at >= semana_atras)
        )
        total_pesquisas_mes = await db.scalar(
            select(func.count(SearchLog.id)).where(SearchLog.searched_at >= mes_atras)
        )
        total_pesquisas_geral = await db.scalar(select(func.count(SearchLog.id)))

        # CARs únicos
        total_cars_unicos = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code)))
        )

        # CARs com problemas
        total_cars_com_problemas = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(
                or_(
                    SearchLog.has_prodes == True,
                    SearchLog.has_embargo_sema == True,
                    SearchLog.has_deforestation == True
                )
            )
        )

        cars_com_prodes = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(SearchLog.has_prodes == True)
        )
        cars_com_embargo = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(SearchLog.has_embargo_sema == True)
        )
        cars_com_desmatamento = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(SearchLog.has_deforestation == True)
        )

        return OverviewMetricas(
            total_clientes=total_clientes or 0,
            clientes_ativos=clientes_ativos or 0,
            clientes_inativos=clientes_inativos or 0,
            clientes_pendentes=clientes_pendentes or 0,
            total_pesquisas_hoje=total_pesquisas_hoje or 0,
            total_pesquisas_semana=total_pesquisas_semana or 0,
            total_pesquisas_mes=total_pesquisas_mes or 0,
            total_pesquisas_geral=total_pesquisas_geral or 0,
            total_cars_unicos=total_cars_unicos or 0,
            total_cars_com_problemas=total_cars_com_problemas or 0,
            cars_com_prodes=cars_com_prodes or 0,
            cars_com_embargo=cars_com_embargo or 0,
            cars_com_desmatamento=cars_com_desmatamento or 0,
        )

    @staticmethod
    async def get_pesquisas_por_dia(db: AsyncSession, dias: int = 30) -> List[PesquisasPorDia]:
        """Obtém pesquisas agrupadas por dia (últimos N dias)."""
        data_limite = datetime.utcnow() - timedelta(days=dias)

        results = await db.execute(
            select(
                func.date(SearchLog.searched_at).label("data"),
                func.count(SearchLog.id).label("quantidade")
            )
            .where(SearchLog.searched_at >= data_limite)
            .group_by(func.date(SearchLog.searched_at))
            .order_by(func.date(SearchLog.searched_at))
        )

        return [
            PesquisasPorDia(data=row.data.isoformat(), quantidade=row.quantidade)
            for row in results.all()
        ]

    @staticmethod
    async def get_cars_por_status(db: AsyncSession) -> List[CARsPorStatus]:
        """Obtém distribuição de CARs por status."""
        total_cars = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code)))
        )

        if not total_cars or total_cars == 0:
            return []

        cars_limpos = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(
                and_(
                    SearchLog.has_prodes == False,
                    SearchLog.has_embargo_sema == False,
                    SearchLog.has_deforestation == False
                )
            )
        ) or 0

        cars_prodes = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(SearchLog.has_prodes == True)
        ) or 0

        cars_embargo = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(SearchLog.has_embargo_sema == True)
        ) or 0

        cars_desmatamento = await db.scalar(
            select(func.count(func.distinct(SearchLog.car_code))).where(SearchLog.has_deforestation == True)
        ) or 0

        return [
            CARsPorStatus(categoria="Limpo", quantidade=cars_limpos, percentual=(cars_limpos / total_cars * 100)),
            CARsPorStatus(categoria="PRODES", quantidade=cars_prodes, percentual=(cars_prodes / total_cars * 100)),
            CARsPorStatus(categoria="Embargo", quantidade=cars_embargo, percentual=(cars_embargo / total_cars * 100)),
            CARsPorStatus(categoria="Desmatamento", quantidade=cars_desmatamento, percentual=(cars_desmatamento / total_cars * 100)),
        ]

    @staticmethod
    async def get_top_clientes(db: AsyncSession, limit: int = 10) -> List[TopCliente]:
        """Obtém top N clientes com mais pesquisas."""
        results = await db.execute(
            select(
                Usuario.nome,
                Usuario.email,
                Usuario.limite_consultas,
                func.count(SearchLog.id).label("quantidade_pesquisas")
            )
            .outerjoin(SearchLog, SearchLog.client_id == Usuario.id)
            .group_by(Usuario.id, Usuario.nome, Usuario.email, Usuario.limite_consultas)
            .order_by(func.count(SearchLog.id).desc())
            .limit(limit)
        )

        return [
            TopCliente(
                nome=row.nome,
                email=row.email,
                quantidade_pesquisas=row.quantidade_pesquisas or 0,
                limite_mensal=row.limite_consultas
            )
            for row in results.all()
        ]

    @staticmethod
    async def get_dashboard_graficos(db: AsyncSession) -> DashboardGraficos:
        """Obtém todos os dados para gráficos do dashboard."""
        pesquisas_por_dia = await AdminService.get_pesquisas_por_dia(db)
        cars_por_status = await AdminService.get_cars_por_status(db)
        top_clientes = await AdminService.get_top_clientes(db)

        return DashboardGraficos(
            pesquisas_por_dia=pesquisas_por_dia,
            cars_por_status=cars_por_status,
            top_clientes=top_clientes,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # NOTIFICAÇÕES
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def criar_notificacao(
        db: AsyncSession,
        tipo: str,
        titulo: str,
        mensagem: Optional[str] = None,
        cliente_id: Optional[UUID] = None,
        car_code: Optional[str] = None
    ) -> AdminNotification:
        """Cria uma notificação para o painel admin."""
        notif = AdminNotification(
            type=tipo,
            title=titulo,
            message=mensagem,
            related_client_id=cliente_id,
            related_car=car_code,
            is_read=False
        )
        db.add(notif)
        await db.commit()
        return notif

    @staticmethod
    async def listar_notificacoes(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        apenas_nao_lidas: bool = False
    ) -> Tuple[List[AdminNotification], int]:
        """Lista notificações com paginação."""
        query = select(AdminNotification)

        if apenas_nao_lidas:
            query = query.where(AdminNotification.is_read == False)

        total = await db.scalar(
            select(func.count(AdminNotification.id))
        )

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(AdminNotification.created_at.desc())

        result = await db.execute(query)
        notifs = result.scalars().all()

        return notifs, total

    @staticmethod
    async def contar_notificacoes_nao_lidas(db: AsyncSession) -> int:
        """Conta notificações não lidas."""
        return await db.scalar(
            select(func.count(AdminNotification.id)).where(AdminNotification.is_read == False)
        ) or 0

    @staticmethod
    async def marcar_notificacao_lida(db: AsyncSession, notif_id: UUID) -> AdminNotification:
        """Marca uma notificação como lida."""
        stmt = select(AdminNotification).where(AdminNotification.id == notif_id)
        result = await db.execute(stmt)
        notif = result.scalar_one_or_none()

        if notif:
            notif.is_read = True
            db.add(notif)
            await db.commit()

        return notif
