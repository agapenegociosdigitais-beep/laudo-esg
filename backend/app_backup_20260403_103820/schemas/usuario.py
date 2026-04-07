"""Schemas Pydantic para autentica��o e gerenciamento de usu�rios."""
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
    """Schema para cria��o de novo usu�rio."""
    senha: str = Field(..., min_length=8, description="M�nimo 8 caracteres")


class UsuarioAtualizar(BaseModel):
    """Schema para atualiza��o parcial do usu�rio."""
    nome: Optional[str] = Field(None, min_length=2, max_length=255)
    empresa: Optional[str] = Field(None, max_length=255)
    perfil: Optional[str] = Field(None, pattern="^(produtor|trader|consultor|admin)$")


class UsuarioResposta(UsuarioBase):
    """Schema de resposta com dados do usu�rio (sem senha)."""
    id: uuid.UUID
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Credenciais para login."""
    email: EmailStr
    senha: str


class TokenResposta(BaseModel):
    """Token JWT retornado ap�s login bem-sucedido."""
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResposta
