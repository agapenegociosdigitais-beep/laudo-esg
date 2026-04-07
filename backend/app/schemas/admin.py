"""Schemas Pydantic para endpoints administrativos."""
import uuid
from typing import Optional

from pydantic import BaseModel

from app.schemas.usuario import UsuarioResposta


class UsuarioAdminResposta(UsuarioResposta):
    """Resposta de usuário com campos administrativos."""
    limite_consultas: Optional[int] = None
    consultas_mes_atual: int = 0
    mes_referencia: Optional[str] = None


class AtualizarLimiteRequest(BaseModel):
    """Request para atualizar limite de consultas."""
    limite_consultas: Optional[int] = None


class TopUsuario(BaseModel):
    """Usuário mais ativo do mês."""
    nome: str
    email: str
    consultas_mes: int


class EstatisticasAdmin(BaseModel):
    """Estatísticas gerais da plataforma."""
    total_usuarios: int
    usuarios_ativos: int
    total_analises: int
    analises_mes_atual: int
    cars_consultados: int
    top_usuarios: list[TopUsuario]
