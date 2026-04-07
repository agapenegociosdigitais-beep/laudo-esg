"""
Depend�ncias compartilhadas dos endpoints FastAPI.
Inclui autentica��o JWT e inje��o de sess�o de banco.
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
    Depend�ncia que valida o token JWT e retorna o usu�rio autenticado.
    Levanta HTTP 401 se o token for inv�lido ou o usu�rio n�o existir.
    """
    token = credenciais.credentials
    usuario_id = decodificar_token(token)

    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inv�lido ou expirado. Fa�a login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    resultado = await db.execute(
        select(Usuario).where(Usuario.id == uuid.UUID(usuario_id))
    )
    usuario = resultado.scalar_one_or_none()

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usu�rio n�o encontrado ou inativo.",
        )

    return usuario


# Tipo anotado para reutiliza��o nos endpoints
UsuarioAtual = Annotated[Usuario, Depends(obter_usuario_atual)]
SessaoDB = Annotated[AsyncSession, Depends(get_db)]


async def obter_admin_atual(usuario: UsuarioAtual) -> Usuario:
    """
    Depend�ncia que verifica se o usu�rio autenticado tem perfil admin.
    Levanta HTTP 403 se n�o for admin.
    """
    if usuario.perfil != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return usuario


AdminAtual = Annotated[Usuario, Depends(obter_admin_atual)]
