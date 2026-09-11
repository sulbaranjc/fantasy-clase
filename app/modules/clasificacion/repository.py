"""Acceso a datos del módulo clasificacion.

No hay tabla propia: es una vista calculada sobre `eventos`, `plantillas`
y `alumnos` (igual que las hojas Puntos_Jornada, Clasificacion y
Clasificacion_General del Excel original eran fórmulas, no datos
introducidos a mano)."""
import asyncmy


async def puntos_de_jugador_en_jornada(pool: asyncmy.Pool, alumno_id: int, jornada_id: int) -> int:
    """Equivalente a la hoja Puntos_Jornada del Excel: suma de los puntos
    que un alumno obtuvo COMO JUGADOR en una jornada concreta."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COALESCE(SUM(puntos_otorgados), 0) FROM eventos "
                "WHERE alumno_id = %s AND jornada_id = %s",
                (alumno_id, jornada_id),
            )
            (total,) = await cur.fetchone()
            return total
