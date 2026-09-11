"""Acceso a datos del módulo profesores.

No hay router propio: con un único profesor por instalación (no es un
sistema multi-profesor), no hace falta una gestión CRUD vía web. La
cuenta se crea con `scripts/crear_profesor.py`; este repositorio lo usa
ese script y el módulo `auth` para el login.
"""
import asyncmy


async def obtener_por_username(pool: asyncmy.Pool, username: str) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                "SELECT id, nombre, username, password_hash FROM profesores WHERE username = %s",
                (username,),
            )
            return await cur.fetchone()


async def crear(pool: asyncmy.Pool, nombre: str, username: str, password_hash: str) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO profesores (nombre, username, password_hash) VALUES (%s, %s, %s)",
                (nombre, username, password_hash),
            )
            return cur.lastrowid
