"""Lógica de negocio del módulo jornadas.

`generar_calendario` es la función pura (sin FastAPI ni SQL) que reproduce
la fórmula del Excel original (=MIN(B5+13,$B$2), jornada de 2 semanas con
la última recortada para cuadrar con el fin de temporada). Se cubre con
pruebas unitarias que reproducen el calendario real de "Fantasy_Clase.xlsx".
"""
from datetime import date, datetime, time, timedelta

import asyncmy

from modules.clases import repository as clases_repository
from modules.jornadas import repository


class ClaseInexistenteError(Exception):
    """No existe la clase para la que se pide generar el calendario."""


class CalendarioYaGeneradoError(Exception):
    """La clase ya tiene jornadas generadas; no se vuelve a generar encima."""


def generar_calendario(fecha_inicio: date, fecha_fin: date, duracion_jornada_dias: int,
                        ventana_fichaje_horas: int) -> list[dict]:
    """Calendario de jornadas consecutivas de `duracion_jornada_dias` días,
    desde `fecha_inicio` hasta `fecha_fin` inclusive. La última jornada se
    recorta para no sobrepasar `fecha_fin` (puede durar menos de lo normal).

    Cada jornada abre su ventana de fichajes en su fecha de inicio (00:00)
    y la cierra `ventana_fichaje_horas` horas después.
    """
    jornadas = []
    numero = 1
    inicio_jornada = fecha_inicio

    while inicio_jornada <= fecha_fin:
        fin_jornada = min(inicio_jornada + timedelta(days=duracion_jornada_dias - 1), fecha_fin)
        apertura = datetime.combine(inicio_jornada, time.min)
        cierre = apertura + timedelta(hours=ventana_fichaje_horas)

        jornadas.append({
            "numero": numero,
            "fecha_inicio": inicio_jornada,
            "fecha_fin": fin_jornada,
            "apertura_fichajes": apertura,
            "cierre_fichajes": cierre,
        })

        inicio_jornada = fin_jornada + timedelta(days=1)
        numero += 1

    return jornadas


async def generar_y_guardar_calendario(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    clase = await clases_repository.obtener_por_id(pool, clase_id)
    if clase is None:
        raise ClaseInexistenteError(f"No existe la clase {clase_id}.")

    if await repository.contar_por_clase(pool, clase_id) > 0:
        raise CalendarioYaGeneradoError(
            "Esta clase ya tiene un calendario de jornadas generado."
        )

    jornadas = generar_calendario(
        clase["fecha_inicio"], clase["fecha_fin"],
        clase["duracion_jornada_dias"], clase["ventana_fichaje_horas"],
    )
    await repository.crear_lote(pool, clase_id, jornadas)
    return await repository.listar_por_clase(pool, clase_id)


async def listar_jornadas(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    return await repository.listar_por_clase(pool, clase_id)


async def obtener_jornada(pool: asyncmy.Pool, jornada_id: int) -> dict | None:
    return await repository.obtener_por_id(pool, jornada_id)


def obtener_jornada_con_ventana_abierta(jornadas: list[dict], ahora: datetime) -> dict | None:
    """De una lista de jornadas, la que tiene la ventana de fichajes
    abierta en el instante `ahora` (o None si ninguna la tiene).

    Función pura: no repite la lógica de negocio de "ventana abierta" del
    módulo plantillas (esa vive allí, aplicada al fichaje en sí); esta es
    la versión de solo lectura que usa el dashboard del alumno para saber
    a qué jornada llevarlo a fichar, sin acoplar jornadas a plantillas.
    """
    for jornada in jornadas:
        if jornada["apertura_fichajes"] <= ahora <= jornada["cierre_fichajes"]:
            return jornada
    return None


async def obtener_jornada_activa(pool: asyncmy.Pool, clase_id: int, ahora: datetime | None = None) -> dict | None:
    ahora = ahora or datetime.now()
    jornadas = await repository.listar_por_clase(pool, clase_id)
    return obtener_jornada_con_ventana_abierta(jornadas, ahora)
