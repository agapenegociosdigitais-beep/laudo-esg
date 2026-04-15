"""Schemas Pydantic para endpoints administrativos."""
import uuid
from datetime import datetime
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


class AnaliseAdminResposta(BaseModel):
    """Análise vista pelo admin."""
    id: uuid.UUID
    numero_car: str
    nome_propriedade: Optional[str] = None
    usuario_email: Optional[str] = None
    status: str
    score_esg: Optional[float] = None
    nivel_risco: Optional[str] = None
    criado_em: datetime


class StatusAPI(BaseModel):
    """Status de uma API externa."""
    online: bool
    latencia_ms: Optional[int] = None
    ultima_verificacao: datetime


class StatusAPIsExternas(BaseModel):
    """Status de todas as APIs externas."""
    ibama: StatusAPI
    semas: StatusAPI
    prodes: StatusAPI
