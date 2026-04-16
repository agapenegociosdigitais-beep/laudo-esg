"""Schemas Pydantic para endpoints administrativos."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

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


class AlertaAnalise(BaseModel):
    """Análise com alertas críticos (embargo, desmatamento, risco alto)."""
    id: uuid.UUID
    numero_car: str
    nome_propriedade: Optional[str] = None
    status: str
    score_esg: Optional[float] = None
    nivel_risco: Optional[str] = None
    criado_em: datetime
    tem_embargo_ibama: bool
    tem_embargo_semas: bool
    tem_desmatamento: bool
    area_desmatada_ha: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class CARProdes(BaseModel):
    """CAR com desmatamento detectado (PRODES)."""
    numero_car: str
    municipio: Optional[str] = None
    area_total_ha: Optional[float] = None
    area_desmatada_ha: Optional[float] = None
    percentual_afetado: Optional[float] = None
    ano_deteccao: Optional[int | str] = None
    bioma: Optional[str] = None
    usuario_email: Optional[str] = None
    criado_em: datetime


class CAREmbargoSemas(BaseModel):
    """CAR com embargo ativo na SEMAS."""
    numero_car: str
    municipio: Optional[str] = None
    numero_tad: Optional[str] = None
    processo: Optional[str] = None
    data_embargo: Optional[str] = None
    situacao: Optional[str] = None
    area_embargada_ha: Optional[float] = None
    usuario_email: Optional[str] = None
    criado_em: datetime


class CarMultiploProblema(BaseModel):
    """CAR que aparece em 2+ categorias de problemas."""
    numero_car: str
    municipio: Optional[str] = None
    nivel_risco: Optional[str] = None
    score_esg: Optional[float] = None
    flags: list[str]


class EvolucaoMensal(BaseModel):
    """Evolução de CARs problemáticos por mês."""
    mes: str
    prodes: int = 0
    embargo_semas: int = 0
    desmatamento: int = 0


class DistribuicaoTipo(BaseModel):
    """Distribuição de CARs por tipo de problema."""
    tipo: str
    total: int


class ResumoCARsProblematicos(BaseModel):
    """Resumo consolidado de CARs com problemas."""
    total_prodes: int = 0
    total_embargo_semas: int = 0
    total_desmatamento: int = 0
    multiplos_problemas: list[CarMultiploProblema] = []
    evolucao_mensal: list[EvolucaoMensal] = []
    distribuicao_tipo: list[DistribuicaoTipo] = []
