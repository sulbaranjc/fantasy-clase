"""Lógica de negocio del módulo plantillas: el corazón del "fantasy".

`excede_presupuesto` y `esta_dentro_de_ventana` son funciones puras (sin
FastAPI ni SQL), cubiertas por pruebas unitarias. El resto orquesta las
llamadas a los repositorios de este módulo y de alumnos/jornadas/clases
para aplicar las reglas que sí dependen de datos reales.
"""
from datetime import datetime

import asyncmy

from modules.alumnos import repository as alumnos_repository
from modules.clases import repository as clases_repository
from modules.jornadas import repository as jornadas_repository
from modules.plantillas import repository
from modules.plantillas.schemas import PlantillaCreate


class JornadaInvalidaError(Exception):
    """La jornada no existe o no pertenece a la clase de la plantilla."""


class FueraDeVentanaError(Exception):
    """Se intenta fichar fuera de la ventana de 24h de la jornada."""


class AlumnoInvalidoError(Exception):
    """El manager o alguno de los jugadores no existe o no pertenece a la clase."""


class PresupuestoExcedidoError(Exception):
    """La suma de valores de los 5 jugadores supera el presupuesto del manager."""


def excede_presupuesto(valores: list[int], presupuesto_manager: int) -> bool:
    return sum(valores) > presupuesto_manager


def esta_dentro_de_ventana(ahora: datetime, apertura: datetime, cierre: datetime) -> bool:
    return apertura <= ahora <= cierre


async def _cargar_y_validar_jugadores(pool: asyncmy.Pool, clase_id: int,
                                       jugadores_ids: list[int]) -> list[dict]:
    jugadores = []
    for jugador_id in jugadores_ids:
        jugador = await alumnos_repository.obtener_por_id(pool, jugador_id)
        if jugador is None or jugador["clase_id"] != clase_id:
            raise AlumnoInvalidoError(f"El alumno {jugador_id} no pertenece a esta clase.")
        jugadores.append(jugador)
    return jugadores


async def fichar_plantilla(pool: asyncmy.Pool, clase_id: int, datos: PlantillaCreate,
                            ahora: datetime | None = None) -> int:
    """Crea la plantilla de un manager para una jornada, o la reemplaza por
    completo si ya tenía una (puede cambiar de opinión mientras la ventana
    de fichajes siga abierta).

    `ahora` solo existe para que las pruebas unitarias/de servicio puedan
    fijar el instante sin depender del reloj real; los endpoints HTTP
    siempre lo dejan en None, que usa `datetime.now()`.
    """
    ahora = ahora or datetime.now()

    jornada = await jornadas_repository.obtener_por_id(pool, datos.jornada_id)
    if jornada is None or jornada["clase_id"] != clase_id:
        raise JornadaInvalidaError(f"La jornada {datos.jornada_id} no pertenece a esta clase.")

    if not esta_dentro_de_ventana(ahora, jornada["apertura_fichajes"], jornada["cierre_fichajes"]):
        raise FueraDeVentanaError(
            "La ventana de fichajes de esta jornada no está abierta "
            f"({jornada['apertura_fichajes']} - {jornada['cierre_fichajes']})."
        )

    clase = await clases_repository.obtener_por_id(pool, clase_id)

    manager = await alumnos_repository.obtener_por_id(pool, datos.manager_id)
    if manager is None or manager["clase_id"] != clase_id:
        raise AlumnoInvalidoError(f"El manager {datos.manager_id} no pertenece a esta clase.")

    jugadores = await _cargar_y_validar_jugadores(pool, clase_id, datos.jugadores_ids)
    valores = [j["valor_actual"] for j in jugadores]

    if excede_presupuesto(valores, clase["presupuesto_manager"]):
        raise PresupuestoExcedidoError(
            f"La plantilla vale {sum(valores)}, supera el presupuesto de {clase['presupuesto_manager']}."
        )

    jugadores_con_valor = [(j["id"], j["valor_actual"]) for j in jugadores]
    existente = await repository.obtener_por_jornada_y_manager(pool, datos.jornada_id, datos.manager_id)

    if existente is not None:
        await repository.reemplazar_jugadores(pool, existente["id"], datos.capitan_id, jugadores_con_valor)
        return existente["id"]

    return await repository.crear(
        pool, datos.jornada_id, datos.manager_id, datos.capitan_id,
        jugadores_con_valor, generada_automaticamente=False,
    )


async def heredar_plantilla_anterior(pool: asyncmy.Pool, jornada_actual_id: int,
                                      jornada_anterior_id: int, manager_id: int) -> int | None:
    """Repite la plantilla de la jornada anterior de un manager en la
    jornada actual, con los valores de mercado vigentes en este momento.

    Pensada para dispararse al cerrar la ventana de fichajes de una
    jornada, sobre los managers que no hayan fichado a tiempo. La propia
    orquestación automática (cuándo y por quién se llama a esta función)
    es una pieza de infraestructura pendiente para la fase de despliegue.

    Devuelve None si el manager tampoco tenía plantilla en la jornada
    anterior (nada que heredar); no hace nada si ya tiene plantilla en la
    jornada actual (ya fichó, no se sobrescribe).
    """
    ya_tiene = await repository.obtener_por_jornada_y_manager(pool, jornada_actual_id, manager_id)
    if ya_tiene is not None:
        return ya_tiene["id"]

    anterior = await repository.obtener_por_jornada_y_manager(pool, jornada_anterior_id, manager_id)
    if anterior is None:
        return None

    jugadores_anteriores = await repository.obtener_jugadores(pool, anterior["id"])
    jugadores_con_valor_actual = []
    for jugador in jugadores_anteriores:
        alumno = await alumnos_repository.obtener_por_id(pool, jugador["jugador_id"])
        jugadores_con_valor_actual.append((jugador["jugador_id"], alumno["valor_actual"]))

    return await repository.crear(
        pool, jornada_actual_id, manager_id, anterior["capitan_id"],
        jugadores_con_valor_actual, generada_automaticamente=True,
    )


async def obtener_plantilla_con_jugadores(pool: asyncmy.Pool, plantilla_id: int) -> dict | None:
    plantilla = await repository.obtener_por_id(pool, plantilla_id)
    if plantilla is None:
        return None
    plantilla["jugadores"] = await repository.obtener_jugadores(pool, plantilla_id)
    return plantilla


async def obtener_plantilla_de_manager(pool: asyncmy.Pool, jornada_id: int, manager_id: int) -> dict | None:
    plantilla = await repository.obtener_por_jornada_y_manager(pool, jornada_id, manager_id)
    if plantilla is None:
        return None
    plantilla["jugadores"] = await repository.obtener_jugadores(pool, plantilla["id"])
    return plantilla


async def listar_plantillas_de_jornada(pool: asyncmy.Pool, jornada_id: int) -> list[dict]:
    plantillas = await repository.listar_por_jornada(pool, jornada_id)
    for plantilla in plantillas:
        plantilla["jugadores"] = await repository.obtener_jugadores(pool, plantilla["id"])
    return plantillas
