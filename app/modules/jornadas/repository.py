"""Acceso a datos del módulo jornadas: único lugar del proyecto donde se
escribe SQL para esta entidad. Sin ORM, por decisión del proyecto."""
import asyncmy

_COLUMNAS = "id, clase_id, numero, fecha_inicio, fecha_fin, apertura_fichajes, cierre_fichajes, cerrada"


async def contar_por_clase(pool: asyncmy.Pool, clase_id: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM jornadas WHERE clase_id = %s", (clase_id,))
            (total,) = await cur.fetchone()
            return total


async def crear_lote(pool: asyncmy.Pool, clase_id: int, jornadas: list[dict]) -> None:
    """Inserta de una vez todas las jornadas generadas para una clase."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO jornadas (
                    clase_id, numero, fecha_inicio, fecha_fin,
                    apertura_fichajes, cierre_fichajes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (clase_id, j["numero"], j["fecha_inicio"], j["fecha_fin"],
                     j["apertura_fichajes"], j["cierre_fichajes"])
                    for j in jornadas
                ],
            )


async def listar_por_clase(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS} FROM jornadas WHERE clase_id = %s ORDER BY numero",
                (clase_id,),
            )
            return await cur.fetchall()


async def obtener_por_id(pool: asyncmy.Pool, jornada_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(f"SELECT {_COLUMNAS} FROM jornadas WHERE id = %s", (jornada_id,))
            return await cur.fetchone()


async def actualizar_ventana_fichajes(pool: asyncmy.Pool, jornada_id: int,
                                       apertura_fichajes, cierre_fichajes) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE jornadas SET apertura_fichajes = %s, cierre_fichajes = %s WHERE id = %s",
                (apertura_fichajes, cierre_fichajes, jornada_id),
            )
