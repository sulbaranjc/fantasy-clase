"""Lógica de negocio del módulo eventos.

`validar_consistencia` es la función pura (sin FastAPI ni SQL) que decide
si un evento tiene sentido: que el alumno, la jornada y el tipo de evento
pertenezcan todos a la misma clase, y que el tipo de evento siga activo.
Se cubre con pruebas unitarias que no tocan la base de datos.
"""
import asyncmy

from modules.alumnos import repository as alumnos_repository
from modules.catalogo_puntos import repository as catalogo_repository
from modules.eventos import repository
from modules.eventos.schemas import EventoCreate, EventoUpdate
from modules.jornadas import repository as jornadas_repository


class AlumnoInvalidoError(Exception):
    """El alumno no existe o no pertenece a la clase del evento."""


class JornadaInvalidaError(Exception):
    """La jornada no existe o no pertenece a la clase del evento."""


class TipoEventoInvalidoError(Exception):
    """El tipo de evento no existe, no pertenece a la clase, o está inactivo."""


class EventoInexistenteError(Exception):
    """No existe el evento sobre el que se intenta operar."""


def validar_consistencia(clase_id: int, alumno: dict | None, jornada: dict | None,
                          catalogo_punto: dict | None) -> None:
    if alumno is None or alumno["clase_id"] != clase_id:
        raise AlumnoInvalidoError("El alumno no pertenece a esta clase.")
    if jornada is None or jornada["clase_id"] != clase_id:
        raise JornadaInvalidaError("La jornada no pertenece a esta clase.")
    if catalogo_punto is None or catalogo_punto["clase_id"] != clase_id:
        raise TipoEventoInvalidoError("El tipo de evento no pertenece a esta clase.")
    if not catalogo_punto["activo"]:
        raise TipoEventoInvalidoError("Este tipo de evento está desactivado.")


async def crear_evento(pool: asyncmy.Pool, clase_id: int, datos: EventoCreate) -> int:
    alumno = await alumnos_repository.obtener_por_id(pool, datos.alumno_id)
    jornada = await jornadas_repository.obtener_por_id(pool, datos.jornada_id)
    catalogo_punto = await catalogo_repository.obtener_por_id(pool, datos.catalogo_punto_id)
    validar_consistencia(clase_id, alumno, jornada, catalogo_punto)

    return await repository.crear(
        pool, clase_id, datos.alumno_id, datos.jornada_id, datos.catalogo_punto_id,
        datos.fecha, datos.nota_numerica, datos.comentario, catalogo_punto["puntos"],
    )


async def actualizar_evento(pool: asyncmy.Pool, evento_id: int, datos: EventoUpdate) -> None:
    evento = await repository.obtener_por_id(pool, evento_id)
    if evento is None:
        raise EventoInexistenteError(f"No existe el evento {evento_id}.")

    catalogo_punto = await catalogo_repository.obtener_por_id(pool, datos.catalogo_punto_id)
    if catalogo_punto is None or catalogo_punto["clase_id"] != evento["clase_id"]:
        raise TipoEventoInvalidoError("El tipo de evento no pertenece a esta clase.")
    if not catalogo_punto["activo"]:
        raise TipoEventoInvalidoError("Este tipo de evento está desactivado.")

    # Corregir un evento de una jornada ya cerrada es una edición retroactiva:
    # el recálculo en cascada del valor de mercado y la clasificación se
    # dispara desde el módulo de jornadas/clasificación cuando exista.
    await repository.actualizar(
        pool, evento_id, datos.catalogo_punto_id, datos.fecha,
        datos.nota_numerica, datos.comentario, catalogo_punto["puntos"],
    )


async def eliminar_evento(pool: asyncmy.Pool, evento_id: int) -> None:
    await repository.eliminar(pool, evento_id)


async def obtener_evento(pool: asyncmy.Pool, evento_id: int) -> dict | None:
    return await repository.obtener_por_id(pool, evento_id)


async def listar_eventos_de_alumno(pool: asyncmy.Pool, alumno_id: int) -> list[dict]:
    return await repository.listar_por_alumno(pool, alumno_id)


async def listar_eventos_de_jornada(pool: asyncmy.Pool, jornada_id: int) -> list[dict]:
    return await repository.listar_por_jornada(pool, jornada_id)
