"""Schemas Pydantic para gera��o e download de relat�rios PDF."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RelatorioRequest(BaseModel):
    """Request para gerar relat�rio PDF de uma an�lise."""
    analise_id: uuid.UUID


class RelatorioResposta(BaseModel):
    """Metadados de um relat�rio gerado."""
    id: uuid.UUID
    nome_arquivo: str
    status: str
    tamanho_bytes: Optional[int] = None
    criado_em: datetime
    url_download: Optional[str] = None

    model_config = {"from_attributes": True}
