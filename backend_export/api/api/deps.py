"""
Dependncias compartilhadas dos endpoints FastAPI.
Inclui autenticao JWT e injeo de sesso de banco.
"""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decodificar_token
from app.models.usuario import Usuario

# Esquema Bearer Token
seguranca = HTTPBearer()


async def obter_usuario_atual(
    credenciais: Annotated[HTTPAuthorizationCredentials, Depends(seguranca)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Usuario:
    """
    Dependncia que valida o token JWT e retorna o usurio autenticado.
    Levanta HTTP 401 se o token for invlido ou o usurio no existir.
    """
    token = credenciais.credentials
    usuario_id = decodificar_token(token)

    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invlido ou expirado. Faa login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    resultado = await db.execute(
        select(Usuario).where(Usuario.id == uuid.UUID(usuario_id))
    )
    usuario = resultado.scalar_one_or_none()

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usurio no encontrado ou inativo.",
        )

    return usuario


# Tipo anotado para reutilizao nos endpoints
UsuarioAtual = Annotated[Usuario, Depends(obter_usuario_atual)]
SessaoDB = Annotated[AsyncSession, Depends(get_db)]
