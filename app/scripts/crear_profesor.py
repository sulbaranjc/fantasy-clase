"""Crea la cuenta de profesor inicial (no hay alta por API: solo hay un
profesor por instalación, no es un sistema multi-profesor).

Uso (con los contenedores levantados), sin argumentos usa una contraseña
GENÉRICA pensada solo para las primeras pruebas — cámbiala en cuanto la
app tenga una pantalla de "cambiar contraseña", o pasa la tuya propia:

    docker compose exec app python -m scripts.crear_profesor
    docker compose exec app python -m scripts.crear_profesor "Álvaro" alvaro "otra-contraseña"
"""
import asyncio
import sys

from core.database import close_pool, init_pool
from core.security import hash_password
from modules.profesores import repository

NOMBRE_POR_DEFECTO = "Álvaro"
USERNAME_POR_DEFECTO = "alvaro"
PASSWORD_GENERICA_DE_PRUEBAS = "cambiar123"  # solo para arrancar; no usar en producción


async def crear_profesor(nombre: str, username: str, password: str) -> None:
    pool = await init_pool()
    try:
        existente = await repository.obtener_por_username(pool, username)
        if existente is not None:
            print(f"Ya existe un profesor con el usuario «{username}» (id={existente['id']}).")
            return
        profesor_id = await repository.crear(pool, nombre, username, hash_password(password))
        print(f"Profesor «{nombre}» creado con id={profesor_id}, usuario «{username}».")
        if password == PASSWORD_GENERICA_DE_PRUEBAS:
            print(f"Contraseña genérica de pruebas: {password} (cámbiala cuanto antes).")
    finally:
        await close_pool()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and len(args) != 3:
        print("Uso: python -m scripts.crear_profesor [<nombre> <usuario> <contraseña>]")
        sys.exit(1)
    nombre_arg, username_arg, password_arg = args or (NOMBRE_POR_DEFECTO, USERNAME_POR_DEFECTO, PASSWORD_GENERICA_DE_PRUEBAS)
    asyncio.run(crear_profesor(nombre_arg, username_arg, password_arg))
