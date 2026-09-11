"""Acceso a datos del módulo eventos: único lugar del proyecto donde se
escribe SQL para esta entidad. Sin ORM, por decisión del proyecto."""
from datetime import date

import asyncmy

_COLUMNAS = (
    "id, clase_id, alumno_id, jornada_id, catalogo_punto_id, fecha, "
    "nota_numerica, comentario, puntos_otorgados"
)


async def crear(pool: asyncmy.Pool, clase_id: int, alumno_id: int, jornada_id: int,
                 catalogo_punto_id: int, fecha: date, nota_numerica: float | None,
                 comentario: str | None, puntos_otorgados: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO eventos (
                    clase_id, alumno_id, jornada_id, catalogo_punto_id,
                    fecha, nota_numerica, comentario, puntos_otorgados
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (clase_id, alumno_id, jornada_id, catalogo_punto_id,
                 fecha, nota_numerica, comentario, puntos_otorgados),
            )
            return cur.lastrowid


async def obtener_por_id(pool: asyncmy.Pool, evento_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(f"SELECT {_COLUMNAS} FROM eventos WHERE id = %s", (evento_id,))
            return await cur.fetchone()


async def listar_por_alumno(pool: asyncmy.Pool, alumno_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS} FROM eventos WHERE alumno_id = %s ORDER BY fecha DESC, id DESC",
                (alumno_id,),
            )
            return await cur.fetchall()


async def listar_por_jornada(pool: asyncmy.Pool, jornada_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS} FROM eventos WHERE jornada_id = %s ORDER BY fecha, id",
                (jornada_id,),
            )
            return await cur.fetchall()


async def actualizar(pool: asyncmy.Pool, evento_id: int, catalogo_punto_id: int,
                      fecha: date, nota_numerica: float | None, comentario: str | None,
                      puntos_otorgados: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE eventos
                SET catalogo_punto_id = %s, fecha = %s, nota_numerica = %s,
                    comentario = %s, puntos_otorgados = %s
                WHERE id = %s
                """,
                (catalogo_punto_id, fecha, nota_numerica, comentario, puntos_otorgados, evento_id),
            )


async def eliminar(pool: asyncmy.Pool, evento_id: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM eventos WHERE id = %s", (evento_id,))
