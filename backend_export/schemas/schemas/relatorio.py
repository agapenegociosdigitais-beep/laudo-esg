"""Schemas Pydantic para gerao e download de relatrios PDF."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RelatorioRequest(BaseModel):
    """Request para gerar relatrio PDF de uma anlise."""
    analise_id: uuid.UUID


class RelatorioResposta(BaseModel):
    """Metadados de um relatrio gerado."""
    id: uuid.UUID
    nome_arquivo: str
    status: str
    tamanho_bytes: Optional[int] = None
    criado_em: datetime
    url_download: Optional[str] = None

    model_config = {"from_attributes": True}
