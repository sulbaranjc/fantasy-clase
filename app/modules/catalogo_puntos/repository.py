"""Acceso a datos del módulo catalogo_puntos: único lugar del proyecto
donde se escribe SQL para esta entidad. Sin ORM, por decisión del proyecto.
"""
import asyncmy

_COLUMNAS = "id, clase_id, nombre, puntos, activo"


async def crear(pool: asyncmy.Pool, clase_id: int, nombre: str, puntos: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO catalogo_puntos (clase_id, nombre, puntos) VALUES (%s, %s, %s)",
                (clase_id, nombre, puntos),
            )
            return cur.lastrowid


async def listar_por_clase(pool: asyncmy.Pool, clase_id: int, solo_activos: bool) -> list[dict]:
    condicion = "AND activo = TRUE" if solo_activos else ""
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS} FROM catalogo_puntos WHERE clase_id = %s {condicion} ORDER BY nombre",
                (clase_id,),
            )
            return await cur.fetchall()


async def obtener_por_id(pool: asyncmy.Pool, catalogo_punto_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS} FROM catalogo_puntos WHERE id = %s", (catalogo_punto_id,)
            )
            return await cur.fetchone()


async def actualizar(pool: asyncmy.Pool, catalogo_punto_id: int, nombre: str,
                      puntos: int, activo: bool) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE catalogo_puntos SET nombre = %s, puntos = %s, activo = %s WHERE id = %s",
                (nombre, puntos, activo, catalogo_punto_id),
            )
