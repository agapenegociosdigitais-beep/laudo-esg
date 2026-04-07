import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import get_settings

settings = get_settings()


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    senha_bytes = senha_plana.encode('utf-8')
    hash_bytes = senha_hash.encode('utf-8') if isinstance(senha_hash, str) else senha_hash
    return bcrypt.checkpw(senha_bytes, hash_bytes)


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')


def criar_token_acesso(subject: str, expira_em=None):
    agora = datetime.now(timezone.utc)
    expiracao = agora + (expira_em or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {'sub': str(subject), 'exp': expiracao, 'iat': agora}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get('sub')
    except JWTError:
        return None
