"""Acceso a datos del módulo alumnos: único lugar del proyecto donde se
escribe SQL para esta entidad. Sin ORM, por decisión del proyecto."""
import asyncmy


async def listar_por_clase(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                """
                SELECT id, nombre, username, valor_actual
                FROM alumnos
                WHERE clase_id = %s
                ORDER BY nombre
                """,
                (clase_id,),
            )
            return await cur.fetchall()


async def obtener_por_id(pool: asyncmy.Pool, alumno_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                "SELECT id, clase_id, nombre, username, password_hash, valor_actual "
                "FROM alumnos WHERE id = %s",
                (alumno_id,),
            )
            return await cur.fetchone()


async def crear(pool: asyncmy.Pool, clase_id: int, nombre: str, username: str,
                 password_hash: str, valor_inicial: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO alumnos (clase_id, nombre, username, password_hash, valor_actual)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (clase_id, nombre, username, password_hash, valor_inicial),
            )
            return cur.lastrowid


async def actualizar_valor(pool: asyncmy.Pool, alumno_id: int, nuevo_valor: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE alumnos SET valor_actual = %s WHERE id = %s",
                (nuevo_valor, alumno_id),
            )
