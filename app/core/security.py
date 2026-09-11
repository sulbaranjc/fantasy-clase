"""Hashing de contraseñas y emisión/validación de JWT en cookie.

Estándar mínimo acordado para esta primera versión: sin límite de intentos
de login ni cambio forzado de contraseña (bajo riesgo: app interna, 24
alumnos por clase).
"""
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

COOKIE_NAME = "fantasy_session"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """False ante cualquier hash que passlib no reconozca (por ejemplo,
    un dato corrupto o sembrado a mano), en vez de dejar escapar la
    excepción interna de passlib: un password_hash inválido debe tratarse
    igual que una contraseña incorrecta, nunca como un error 500."""
    try:
        return _pwd_context.verify(password, password_hash)
    except ValueError:
        return False


def crear_token(subject: str, claims: dict | None = None) -> str:
    """Crea un JWT firmado. `subject` identifica al usuario (ej. 'alumno:12')."""
    settings = get_settings()
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.jwt_expira_minutos),
        **(claims or {}),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict:
    """Lanza jwt.PyJWTError si el token es inválido o expiró."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
