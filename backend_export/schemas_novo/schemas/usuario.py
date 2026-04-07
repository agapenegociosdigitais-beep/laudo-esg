"""Schemas Pydantic para autenticao e gerenciamento de usurios."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UsuarioBase(BaseModel):
    email: EmailStr
    nome: str = Field(..., min_length=2, max_length=255)
    empresa: Optional[str] = Field(None, max_length=255)
    perfil: str = Field(default="consultor", pattern="^(produtor|trader|consultor|admin)$")


class UsuarioCriar(UsuarioBase):
    """Schema para criao de novo usurio."""
    senha: str = Field(..., min_length=8, description="Mnimo 8 caracteres")


class UsuarioAtualizar(BaseModel):
    """Schema para atualizao parcial do usurio."""
    nome: Optional[str] = Field(None, min_length=2, max_length=255)
    empresa: Optional[str] = Field(None, max_length=255)
    perfil: Optional[str] = Field(None, pattern="^(produtor|trader|consultor|admin)$")


class UsuarioResposta(UsuarioBase):
    """Schema de resposta com dados do usurio (sem senha)."""
    id: uuid.UUID
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Credenciais para login."""
    email: EmailStr
    senha: str


class TokenResposta(BaseModel):
    """Token JWT retornado aps login bem-sucedido."""
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResposta
