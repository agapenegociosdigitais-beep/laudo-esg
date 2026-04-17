"""Autenticação e segurança para painel administrativo."""
import logging
from datetime import datetime, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer

from app.core.config import get_settings
from app.core.database import get_db
from app.models.admin import AdminUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()

security = HTTPBearer()


class AdminJWT:
    """Gerenciador de tokens JWT para administrador."""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 8 * 60  # 8 horas para admin

    def criar_token(self, admin_id: str) -> str:
        """Cria um token JWT para o administrador."""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(admin_id),  # admin_id em UUID
            "exp": expire,
            "iat": now,
            "type": "admin"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    async def validar_token(self, token: str) -> UUID:
        """Valida um token JWT e retorna o admin_id."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verificar tipo de token
            if payload.get("type") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )

            admin_id = payload.get("sub")
            if not admin_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token mal formatado"
                )

            return UUID(admin_id)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Erro ao validar token JWT: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )


admin_jwt = AdminJWT()


async def obter_admin_atual(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
) -> AdminUser:
    """Dependency para obter o administrador autenticado.

    Extrai token do header Authorization: Bearer <token>

    Raises:
        HTTPException: Se o token for inválido ou o admin não existir
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Extrai token do formato "Bearer <token>"
    token = authorization.split(" ", 1)[1]

    # Validar token
    admin_id = await admin_jwt.validar_token(token)

    # Buscar admin no banco
    stmt = select(AdminUser).where(AdminUser.id == admin_id)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrador não encontrado"
        )

    return admin
