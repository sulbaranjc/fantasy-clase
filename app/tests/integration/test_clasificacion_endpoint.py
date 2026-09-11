"""Pruebas de integración del módulo clasificacion contra MySQL real.

Fichar plantillas exige sesión de alumno; registrar eventos exige sesión
de profesor — los tests alternan la sesión del `cliente` según toque.
"""
from datetime import datetime, timedelta

import pytest

from core.database import get_pool
from modules.jornadas import repository as jornadas_repository

from .conftest import login_como_alumno, login_como_profesor


async def _crear_jornada_abierta(clase_id: int, numero: int) -> int:
    pool = get_pool()
    ahora = datetime.now()
    await jornadas_repository.crear_lote(pool, clase_id, [{
        "numero": numero, "fecha_inicio": ahora.date(), "fecha_fin": ahora.date(),
        "apertura_fichajes": ahora - timedelta(hours=1), "cierre_fichajes": ahora + timedelta(hours=1),
    }])
    jornadas = await jornadas_repository.listar_por_clase(pool, clase_id)
    return next(j["id"] for j in jornadas if j["numero"] == numero)


@pytest.mark.asyncio
async def test_clasificacion_de_jornada_aplica_el_bonus_de_capitan(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids, catalogo_punto_id, profesor_id
):
    manager_a, manager_b, jugador_c, jugador_d, jugador_e = cinco_alumnos_ids

    # Ambos managers fichan a los mismos 5 (fichaje no exclusivo), pero
    # cada uno se nombra capitán a sí mismo.
    for manager_id in (manager_a, manager_b):
        await login_como_alumno(cliente, manager_id)
        respuesta = await cliente.post("/plantillas", json={
            "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id,
        })
        assert respuesta.status_code == 201

    # Solo manager_a (como jugador) puntúa esta jornada: catalogo_punto_id vale 5.
    await login_como_profesor(cliente, profesor_id)
    evento = await cliente.post(
        "/eventos", params={"clase_id": clase_id},
        json={"alumno_id": manager_a, "jornada_id": jornada_abierta_id,
              "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22"},
    )
    assert evento.status_code == 201

    clasificacion = await cliente.get(f"/clasificacion/jornada/{jornada_abierta_id}")
    assert clasificacion.status_code == 200
    por_manager = {c["manager_id"]: c for c in clasificacion.json()}

    # manager_a es su propio capitán: (5+0+0+0+0) + bonus del capitán (5) = 10
    assert por_manager[manager_a]["total"] == 10
    # manager_b se nombra capitán a sí mismo (0 puntos): (5+0+0+0+0) + bonus (0) = 5
    assert por_manager[manager_b]["total"] == 5


@pytest.mark.asyncio
async def test_clasificacion_general_acumula_varias_jornadas(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids, catalogo_punto_id, profesor_id
):
    manager_a = cinco_alumnos_ids[0]
    jornada_2_id = await _crear_jornada_abierta(clase_id, 100)

    for jornada_id in (jornada_abierta_id, jornada_2_id):
        await login_como_alumno(cliente, manager_a)
        await cliente.post("/plantillas", json={
            "jornada_id": jornada_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_a,
        })
        await login_como_profesor(cliente, profesor_id)
        await cliente.post(
            "/eventos", params={"clase_id": clase_id},
            json={"alumno_id": manager_a, "jornada_id": jornada_id,
                  "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22"},
        )

    general = await cliente.get("/clasificacion/general", params={"clase_id": clase_id})
    assert general.status_code == 200
    entrada = next(e for e in general.json() if e["manager_id"] == manager_a)

    # 10 puntos por jornada (ver test anterior) x 2 jornadas = 20
    assert entrada["puntos_totales"] == 20
    assert entrada["posicion"] == 1


@pytest.mark.asyncio
async def test_podio_devuelve_los_tres_primeros(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids, catalogo_punto_id):
    for manager_id in cinco_alumnos_ids:
        await login_como_alumno(cliente, manager_id)
        await cliente.post("/plantillas", json={
            "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id,
        })

    respuesta = await cliente.get("/clasificacion/podio", params={"clase_id": clase_id})

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 3


@pytest.mark.asyncio
async def test_validacion_seleccion_detecta_alumno_no_fichado(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids, alumno_id
):
    # `alumno_id` (fixture) crea un sexto alumno que no participa en ninguna plantilla.
    manager_a = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_a)
    await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_a,
    })

    respuesta = await cliente.get("/clasificacion/validacion-seleccion", params={"clase_id": clase_id})

    assert respuesta.status_code == 200
    por_alumno = {fila["alumno_id"]: fila for fila in respuesta.json()}
    for id_fichado in cinco_alumnos_ids:
        assert por_alumno[id_fichado]["estado"] == "OK"
    assert por_alumno[alumno_id]["estado"] == "NO SELECCIONADO"
    assert por_alumno[alumno_id]["veces_fichado"] == 0
