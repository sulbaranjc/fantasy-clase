"""Lógica de negocio del módulo auth.

`usuario_desde_claims` es la función pura (sin FastAPI ni SQL) que
reconstruye quién está autenticado a partir de los claims ya decodificados
de un JWT, sin volver a tocar la base de datos en cada petición.
"""
import asyncmy

from core.security import crear_token, verify_password
from modules.alumnos import repository as alumnos_repository
from modules.profesores import repository as profesores_repository


class CredencialesInvalidasError(Exception):
    """Usuario o contraseña incorrectos."""


def usuario_desde_claims(claims: dict) -> dict:
    """El `subject` de nuestros tokens tiene la forma "profesor:5" o
    "alumno:12"; el resto del usuario ya viaja en los propios claims para
    no depender de la base de datos en cada petición autenticada."""
    tipo, id_texto = claims["sub"].split(":", maxsplit=1)
    return {
        "tipo": tipo,
        "id": int(id_texto),
        "nombre": claims.get("nombre"),
        "clase_id": claims.get("clase_id"),
    }


async def login_profesor(pool: asyncmy.Pool, username: str, password: str) -> tuple[str, dict]:
    profesor = await profesores_repository.obtener_por_username(pool, username)
    if profesor is None or not verify_password(password, profesor["password_hash"]):
        raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

    usuario = {"tipo": "profesor", "id": profesor["id"], "nombre": profesor["nombre"], "clase_id": None}
    token = crear_token(f"profesor:{profesor['id']}", {"tipo": "profesor", "nombre": profesor["nombre"]})
    return token, usuario


async def login_alumno(pool: asyncmy.Pool, username: str, password: str) -> tuple[str, dict]:
    alumno = await alumnos_repository.obtener_por_username(pool, username)
    if alumno is None or not verify_password(password, alumno["password_hash"]):
        raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

    usuario = {
        "tipo": "alumno", "id": alumno["id"], "nombre": alumno["nombre"], "clase_id": alumno["clase_id"],
    }
    token = crear_token(
        f"alumno:{alumno['id']}",
        {"tipo": "alumno", "nombre": alumno["nombre"], "clase_id": alumno["clase_id"]},
    )
    return token, usuario
