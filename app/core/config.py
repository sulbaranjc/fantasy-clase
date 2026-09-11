"""Configuración de la aplicación, leída de variables de entorno.

Ningún secreto se hardcodea aquí: todo llega vía entorno (ver .env.example
en la raíz del proyecto). pydantic-settings valida tipos y falla rápido si
falta algo obligatorio.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "db"
    db_port: int = 3306
    db_name: str = "fantasy_clase"
    db_user: str = "fantasy_app"
    db_password: str = "changeme_app"

    jwt_secret: str = "changeme_jwt_secret"
    jwt_algorithm: str = "HS256"
    jwt_expira_minutos: int = 60 * 24 * 14  # sesión válida ~2 semanas (una jornada)

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Settings cacheados: se leen las variables de entorno una sola vez."""
    return Settings()
