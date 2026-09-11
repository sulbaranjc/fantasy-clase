"""Lógica de negocio del módulo clases.

La validación de las reglas de negocio de entrada (fechas coherentes, valor
mínimo <= valor inicial) vive en el propio schema Pydantic (`ClaseCreate`),
que es la única fuente de verdad de validación de datos del proyecto.
"""
import asyncmy

from modules.clases import repository
from modules.clases.schemas import ClaseCreate


async def crear_clase(pool: asyncmy.Pool, profesor_id: int, datos: ClaseCreate) -> int:
    return await repository.crear(
        pool,
        profesor_id=profesor_id,
        nombre=datos.nombre,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
        duracion_jornada_dias=datos.duracion_jornada_dias,
        ventana_fichaje_horas=datos.ventana_fichaje_horas,
        valor_inicial_jugador=datos.valor_inicial_jugador,
        valor_minimo_jugador=datos.valor_minimo_jugador,
        factor_recalculo_valor=datos.factor_recalculo_valor,
        presupuesto_manager=datos.presupuesto_manager,
    )


async def listar_clases_de_profesor(pool: asyncmy.Pool, profesor_id: int) -> list[dict]:
    return await repository.listar_por_profesor(pool, profesor_id)


async def obtener_clase(pool: asyncmy.Pool, clase_id: int) -> dict | None:
    return await repository.obtener_por_id(pool, clase_id)
