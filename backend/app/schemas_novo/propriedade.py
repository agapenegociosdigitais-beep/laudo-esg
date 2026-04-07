"""Schemas Pydantic para propriedades rurais e dados do CAR."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PropriedadeBase(BaseModel):
    numero_car: str = Field(..., description="Nmero do CAR (ex: MT-5107248-XXXX...)")
    estado: str = Field(..., min_length=2, max_length=2, description="UF do estado")
    municipio: str
    nome_propriedade: Optional[str] = None
    area_ha: Optional[float] = None
    bioma: Optional[str] = None


class PropriedadeResposta(PropriedadeBase):
    """Resposta completa da propriedade com GeoJSON."""
    id: uuid.UUID
    geojson: Optional[Dict[str, Any]] = None
    status_car: Optional[str] = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class BuscaCARRequest(BaseModel):
    """Request para busca de propriedade pelo nmero do CAR."""
    numero_car: str = Field(..., description="Nmero completo do CAR")


class CARResultado(BaseModel):
    """
    Resultado retornado pelo SICAR para um nmero de CAR.
    Inclui o ID interno do banco para uso imediato na anlise.
    """
    id: Optional[uuid.UUID] = Field(None, description="ID interno (gerado aps salvar no banco)")
    numero_car: str
    estado: str
    municipio: str
    nome_propriedade: Optional[str] = None
    area_ha: Optional[float] = None
    status_car: Optional[str] = None
    bioma: Optional[str] = None
    geojson: Optional[Dict[str, Any]] = None
    fonte: str = Field(default="SICAR", description="Fonte dos dados: SICAR ou Simulado")
    encontrado: bool = True


class PropriedadeLista(BaseModel):
    """Lista paginada de propriedades."""
    total: int
    pagina: int
    itens: List[PropriedadeResposta]
