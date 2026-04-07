"""Schemas Pydantic para anï¿½lises de conformidade ESG, embargos e ï¿½reas protegidas."""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResultadoConformidade(BaseModel):
    """Resultado da verificacao de conformidade para uma regulacao."""
    conforme: bool
    nivel_risco: str = Field(..., description="BAIXO, MEDIO, ALTO, CRITICO")
    detalhe: str
    recomendacoes: List[str] = []


class ResultadoDesmatamento(BaseModel):
    """Resultado da verificação de desmatamento (PRODES/INPE)."""
    desmatamento_detectado: bool
    area_desmatada_ha: float = 0.0
    periodo_referencia: str
    fonte: str = "PRODES/INPE"
    detalhes: Optional[Dict[str, Any]] = None


class AnaliseRequest(BaseModel):
    """Request para iniciar anï¿½lise de uma propriedade."""
    propriedade_id: uuid.UUID
    data_inicio: date = Field(..., description="Inï¿½cio do perï¿½odo de anï¿½lise")
    data_fim: date = Field(..., description="Fim do perï¿½odo de anï¿½lise")


class AnaliseResposta(BaseModel):
    """Resposta completa de uma anï¿½lise."""
    id: uuid.UUID
    propriedade_id: uuid.UUID
    data_inicio: date
    data_fim: date

    # Embargos ambientais
    # Estrutura do dict: {embargado, orgao, numero_embargo, data_embargo,
    #                     area_embargada_ha, motivo, fonte, verificado, status_display}
    embargo_ibama: Optional[Dict[str, Any]] = None
    embargo_semas: Optional[Dict[str, Any]] = None

    # ï¿½reas protegidas
    # Estrutura do dict: {sobreposicao_detectada, tipo_verificacao, nome_area,
    #                     categoria, percentual_sobreposicao, area_sobreposicao_ha,
    #                     esfera, fonte, verificado, status_display}
    sobreposicao_uc: Optional[Dict[str, Any]] = None
    sobreposicao_ti: Optional[Dict[str, Any]] = None

    # Cobertura do solo
    cobertura_solo: Optional[Dict[str, float]] = None

    # Desmatamento
    area_desmatada_ha: Optional[float] = None
    desmatamento_detectado: bool = False

    # Conformidade socioambiental (quilombola, assentamento, trabalho, RL/APP, marco UE)
    resultado_conformidade: Optional[Dict[str, Any]] = None

    # Conformidade
    moratorio_soja_conforme: Optional[bool] = None
    moratorio_soja_detalhe: Optional[str] = None
    eudr_conforme: Optional[bool] = None
    eudr_detalhe: Optional[str] = None

    # Score ESG
    score_esg: Optional[float] = None
    nivel_risco: Optional[str] = None

    # Status
    status: str
    erro_mensagem: Optional[str] = None
    criado_em: datetime

    model_config = {"from_attributes": True}
