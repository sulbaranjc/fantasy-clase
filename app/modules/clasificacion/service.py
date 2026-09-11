"""Lógica de negocio del módulo clasificacion.

`calcular_puntos_manager` y `calcular_ranking` son funciones puras (sin
FastAPI ni SQL), cubiertas por pruebas unitarias. El resto orquesta a
partir de los repositorios de plantillas, alumnos, jornadas y de este
mismo módulo.

Nota de rendimiento: se recorren jornadas y jugadores con consultas
independientes en vez de una única consulta SQL de agregación, para
reutilizar tal cual las funciones ya probadas de `plantillas.service` y
mantener cada módulo dueño de su propio SQL. Con el volumen de esta app
(≈24 alumnos, 12 jornadas por clase) el coste es insignificante; si algún
día hiciera falta, es el punto natural para introducir una consulta
agregada.
"""
import asyncmy

from modules.alumnos import repository as alumnos_repository
from modules.clasificacion import repository
from modules.jornadas import repository as jornadas_repository
from modules.plantillas import service as plantillas_service


def calcular_puntos_manager(puntos_por_jugador: dict[int, int], capitan_id: int) -> int:
    """Puntos de un manager en una jornada: suma de sus 5 jugadores, más un
    bonus igual a los puntos del capitán (se cuenta una vez extra, es
    decir, el capitán "duplica" su aportación)."""
    total = sum(puntos_por_jugador.values())
    bonus_capitan = puntos_por_jugador.get(capitan_id, 0)
    return total + bonus_capitan


def calcular_ranking(totales: list[tuple[int, int]]) -> list[dict]:
    """Ordena de mayor a menor puntuación y asigna posición al estilo
    RANK() de SQL/Excel: los empates comparten posición y la siguiente
    salta el hueco (1, 1, 3, 4 — nunca 1, 1, 2, 3)."""
    ordenado = sorted(totales, key=lambda item: item[1], reverse=True)
    resultado = []
    posicion_actual = 0
    puntos_anteriores = None
    for indice, (manager_id, puntos) in enumerate(ordenado, start=1):
        if puntos != puntos_anteriores:
            posicion_actual = indice
        resultado.append({"manager_id": manager_id, "puntos_totales": puntos, "posicion": posicion_actual})
        puntos_anteriores = puntos
    return resultado


async def _puntos_de_plantilla(pool: asyncmy.Pool, plantilla: dict) -> dict:
    puntos_por_jugador = {
        jugador["jugador_id"]: await repository.puntos_de_jugador_en_jornada(
            pool, jugador["jugador_id"], plantilla["jornada_id"]
        )
        for jugador in plantilla["jugadores"]
    }
    total = calcular_puntos_manager(puntos_por_jugador, plantilla["capitan_id"])
    return {
        "manager_id": plantilla["manager_id"],
        "jornada_id": plantilla["jornada_id"],
        "capitan_id": plantilla["capitan_id"],
        "puntos_jugadores": puntos_por_jugador,
        "total": total,
        "tiene_plantilla": True,
    }


async def clasificacion_de_jornada(pool: asyncmy.Pool, jornada_id: int) -> list[dict]:
    plantillas = await plantillas_service.listar_plantillas_de_jornada(pool, jornada_id)
    resultado = [await _puntos_de_plantilla(pool, plantilla) for plantilla in plantillas]
    resultado.sort(key=lambda entrada: entrada["total"], reverse=True)
    return resultado


async def puntos_de_manager_en_jornada(pool: asyncmy.Pool, jornada_id: int, manager_id: int) -> dict:
    plantilla = await plantillas_service.obtener_plantilla_de_manager(pool, jornada_id, manager_id)
    if plantilla is None:
        return {
            "manager_id": manager_id, "jornada_id": jornada_id, "capitan_id": None,
            "puntos_jugadores": {}, "total": 0, "tiene_plantilla": False,
        }
    return await _puntos_de_plantilla(pool, plantilla)


async def clasificacion_general(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    alumnos = await alumnos_repository.listar_por_clase(pool, clase_id)
    jornadas = await jornadas_repository.listar_por_clase(pool, clase_id)

    totales_por_manager = {alumno["id"]: 0 for alumno in alumnos}
    for jornada in jornadas:
        for entrada in await clasificacion_de_jornada(pool, jornada["id"]):
            totales_por_manager[entrada["manager_id"]] = (
                totales_por_manager.get(entrada["manager_id"], 0) + entrada["total"]
            )

    ranking = calcular_ranking(list(totales_por_manager.items()))
    nombres = {alumno["id"]: alumno["nombre"] for alumno in alumnos}
    for entrada in ranking:
        entrada["nombre"] = nombres.get(entrada["manager_id"], "—")
    return ranking


async def podio(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    return (await clasificacion_general(pool, clase_id))[:3]


async def validar_seleccion_completa(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    """Equivalente a la hoja Validacion_Seleccion del Excel: comprueba, de
    forma ACUMULADA a lo largo de toda la temporada (todas las jornadas
    juntas), que cada alumno haya sido fichado como jugador al menos una
    vez por algún manager."""
    alumnos = await alumnos_repository.listar_por_clase(pool, clase_id)
    jornadas = await jornadas_repository.listar_por_clase(pool, clase_id)

    veces_fichado = {alumno["id"]: 0 for alumno in alumnos}
    for jornada in jornadas:
        for plantilla in await plantillas_service.listar_plantillas_de_jornada(pool, jornada["id"]):
            for jugador in plantilla["jugadores"]:
                if jugador["jugador_id"] in veces_fichado:
                    veces_fichado[jugador["jugador_id"]] += 1

    return [
        {
            "alumno_id": alumno["id"],
            "nombre": alumno["nombre"],
            "veces_fichado": veces_fichado[alumno["id"]],
            "estado": "OK" if veces_fichado[alumno["id"]] > 0 else "NO SELECCIONADO",
        }
        for alumno in alumnos
    ]
