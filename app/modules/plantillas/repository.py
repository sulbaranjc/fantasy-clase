"""Acceso a datos del módulo plantillas: único lugar del proyecto donde se
escribe SQL para esta entidad. Sin ORM, por decisión del proyecto."""
import asyncmy

_COLUMNAS_PLANTILLA = "id, jornada_id, manager_id, capitan_id, generada_automaticamente"


async def obtener_por_id(pool: asyncmy.Pool, plantilla_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS_PLANTILLA} FROM plantillas WHERE id = %s", (plantilla_id,)
            )
            return await cur.fetchone()


async def obtener_por_jornada_y_manager(pool: asyncmy.Pool, jornada_id: int, manager_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS_PLANTILLA} FROM plantillas WHERE jornada_id = %s AND manager_id = %s",
                (jornada_id, manager_id),
            )
            return await cur.fetchone()


async def listar_por_jornada(pool: asyncmy.Pool, jornada_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS_PLANTILLA} FROM plantillas WHERE jornada_id = %s ORDER BY manager_id",
                (jornada_id,),
            )
            return await cur.fetchall()


async def obtener_jugadores(pool: asyncmy.Pool, plantilla_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                "SELECT jugador_id, valor_al_fichar FROM plantilla_jugadores WHERE plantilla_id = %s",
                (plantilla_id,),
            )
            return await cur.fetchall()


async def crear(pool: asyncmy.Pool, jornada_id: int, manager_id: int, capitan_id: int,
                 jugadores_con_valor: list[tuple[int, int]], generada_automaticamente: bool) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO plantillas (jornada_id, manager_id, capitan_id, generada_automaticamente)
                VALUES (%s, %s, %s, %s)
                """,
                (jornada_id, manager_id, capitan_id, generada_automaticamente),
            )
            plantilla_id = cur.lastrowid
            await cur.executemany(
                "INSERT INTO plantilla_jugadores (plantilla_id, jugador_id, valor_al_fichar) VALUES (%s, %s, %s)",
                [(plantilla_id, jugador_id, valor) for jugador_id, valor in jugadores_con_valor],
            )
            return plantilla_id


async def reemplazar_jugadores(pool: asyncmy.Pool, plantilla_id: int, capitan_id: int,
                                jugadores_con_valor: list[tuple[int, int]]) -> None:
    """Sustituye la plantilla completa de un manager (permitido mientras la
    ventana de fichajes siga abierta: puede cambiar de opinión)."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE plantillas SET capitan_id = %s, generada_automaticamente = FALSE WHERE id = %s",
                (capitan_id, plantilla_id),
            )
            await cur.execute("DELETE FROM plantilla_jugadores WHERE plantilla_id = %s", (plantilla_id,))
            await cur.executemany(
                "INSERT INTO plantilla_jugadores (plantilla_id, jugador_id, valor_al_fichar) VALUES (%s, %s, %s)",
                [(plantilla_id, jugador_id, valor) for jugador_id, valor in jugadores_con_valor],
            )
