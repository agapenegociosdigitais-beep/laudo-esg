"""
Configuraes centrais da aplicao Eureka Terra.
Todas as variveis so carregadas do arquivo .env.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # ?Aplicao ?
    APP_NAME: str = "Eureka Terra"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ?Banco de Dados ?
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/eureka_db"

    # ?Cache Redis ?
    REDIS_URL: str = "redis://localhost:6379"

    # ?Segurana JWT ?
    # Em produo, defina SECRET_KEY no .env com um valor gerado por:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @field_validator("SECRET_KEY")
    @classmethod
    def validar_secret_key(cls, v: str) -> str:
        inseguros = {"CHANGE_ME_IN_PRODUCTION", "sua_chave_secreta_jwt_aqui", "secret", ""}
        # A validao  lida antes de ENVIRONMENT, ento verificamos pelo comprimento mnimo
        # e pelos valores conhecidamente inseguros apenas em runtime (via is_producao property).
        if v in inseguros and len(v) < 32:
            import os
            env = os.getenv("ENVIRONMENT", "development")
            if env == "production":
                raise ValueError(
                    "SECRET_KEY insegura em produo. "
                    "Gere uma chave com: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
        return v

    # ?CORS ?
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | List[str]) -> List[str]:
        """Aceita tanto string separada por vrgula quanto lista JSON."""
        if isinstance(v, str):
            # Tenta JSON primeiro; se falhar, separa por vrgula
            try:
                import json
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",")]
        return v

    # ?MapBiomas ?
    MAPBIOMAS_TOKEN: str = ""
    MAPBIOMAS_API_URL: str = "https://api.mapbiomas.org/api/v1"

    # ?SICAR (Sistema de Cadastro Ambiental Rural) ?
    SICAR_API_URL: str = "https://consultapublica.car.gov.br/publico"
    SICAR_TIMEOUT_SEGUNDOS: int = 30

    # ?Relatrios PDF ?
    REPORTS_DIR: str = "/app/reports"

    @property
    def is_producao(self) -> bool:
        """Retorna True se o ambiente for produo."""
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Retorna instncia cacheada das configuraes."""
    return Settings()
