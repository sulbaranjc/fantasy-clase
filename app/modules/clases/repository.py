"""Acceso a datos del módulo clases: único lugar del proyecto donde se
escribe SQL para esta entidad. Sin ORM, por decisión del proyecto."""
from datetime import date

import asyncmy

_COLUMNAS = (
    "id, profesor_id, nombre, fecha_inicio, fecha_fin, duracion_jornada_dias, "
    "ventana_fichaje_horas, valor_inicial_jugador, valor_minimo_jugador, "
    "factor_recalculo_valor, presupuesto_manager, activa"
)


async def crear(pool: asyncmy.Pool, profesor_id: int, nombre: str,
                 fecha_inicio: date, fecha_fin: date, duracion_jornada_dias: int,
                 ventana_fichaje_horas: int, valor_inicial_jugador: int,
                 valor_minimo_jugador: int, factor_recalculo_valor: float,
                 presupuesto_manager: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO clases (
                    profesor_id, nombre, fecha_inicio, fecha_fin,
                    duracion_jornada_dias, ventana_fichaje_horas,
                    valor_inicial_jugador, valor_minimo_jugador,
                    factor_recalculo_valor, presupuesto_manager
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (profesor_id, nombre, fecha_inicio, fecha_fin, duracion_jornada_dias,
                 ventana_fichaje_horas, valor_inicial_jugador, valor_minimo_jugador,
                 factor_recalculo_valor, presupuesto_manager),
            )
            return cur.lastrowid


async def listar_por_profesor(pool: asyncmy.Pool, profesor_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(
                f"SELECT {_COLUMNAS} FROM clases WHERE profesor_id = %s ORDER BY fecha_inicio DESC",
                (profesor_id,),
            )
            return await cur.fetchall()


async def obtener_por_id(pool: asyncmy.Pool, clase_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(f"SELECT {_COLUMNAS} FROM clases WHERE id = %s", (clase_id,))
            return await cur.fetchone()
