from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Porteiro de Chaves: Lê as variáveis do .env (local) ou
    das Environment Variables do Railway (produção).
    """

    # --- Ambiente ---
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # --- Segurança JWT ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # --- Banco de Dados ---
    DATABASE_URL: str

    # --- Apify ---
    APIFY_TOKEN: str

    # --- Mercado Pago ---
    MP_ACCESS_TOKEN: str
    MP_WEBHOOK_SECRET: str = "dev-secret-placeholder"
    MP_PUBLIC_KEY: str = ""
    MP_WEBHOOK_URL: str = "http://localhost:8000"  # Atualizar no Railway com URL real

    # --- Meta (Graph API — Motor 1, opcional na fase inicial) ---
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_allowed_origins(self) -> list[str]:
        """Converte a string de origens separadas por vírgula em lista."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Cache das configurações para não reler o .env a cada requisição.
    Use como dependência do FastAPI: Depends(get_settings)
    """
    return Settings()
