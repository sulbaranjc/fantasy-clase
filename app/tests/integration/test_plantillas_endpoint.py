"""Pruebas de integración del módulo plantillas contra MySQL real.

Fichar exige sesión de alumno (`login_como_alumno`); administrar
(heredar, listar todas las plantillas de una jornada) exige profesor.
"""
from datetime import datetime, timedelta

import pytest

from core.database import get_pool
from modules.alumnos import repository as alumnos_repository
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
async def test_fichar_plantilla_dentro_de_ventana_y_presupuesto(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    manager_id = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_id)

    payload = {
        "jornada_id": jornada_abierta_id,
        "jugadores_ids": cinco_alumnos_ids,
        "capitan_id": manager_id,
    }

    respuesta = await cliente.post("/plantillas", json=payload)

    assert respuesta.status_code == 201
    plantilla = respuesta.json()
    assert plantilla["manager_id"] == manager_id
    assert plantilla["capitan_id"] == manager_id
    assert plantilla["generada_automaticamente"] is False
    assert sorted(j["jugador_id"] for j in plantilla["jugadores"]) == sorted(cinco_alumnos_ids)
    assert all(j["valor_al_fichar"] == 20 for j in plantilla["jugadores"])


@pytest.mark.asyncio
async def test_rechaza_ficharse_a_si_mismo_fuera_de_los_cinco(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids, alumno_id
):
    manager_id = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_id)
    # 5 jugadores distintos que no incluyen al manager (alumno_id es un
    # sexto alumno de la clase, necesario para no repetir ninguno).
    jugadores_sin_manager = cinco_alumnos_ids[1:] + [alumno_id]

    respuesta = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id,
        "jugadores_ids": jugadores_sin_manager,
        "capitan_id": jugadores_sin_manager[0],
    })

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_rechaza_plantilla_que_excede_el_presupuesto(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    # Sube el valor de un jugador para que 20*4 + 100 = 180 > 120 (presupuesto por defecto).
    pool = get_pool()
    await alumnos_repository.actualizar_valor(pool, cinco_alumnos_ids[0], 100)

    manager_id = cinco_alumnos_ids[1]
    await login_como_alumno(cliente, manager_id)

    respuesta = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id,
        "jugadores_ids": cinco_alumnos_ids,
        "capitan_id": manager_id,
    })

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_rechaza_fichar_fuera_de_la_ventana_de_fichajes(cliente, clase_id, jornada_id, cinco_alumnos_ids):
    # `jornada_id` usa el calendario real (temporada 2026/2027); su ventana
    # de fichajes todavía no ha abierto en el momento de correr las pruebas.
    manager_id = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_id)

    respuesta = await cliente.post("/plantillas", json={
        "jornada_id": jornada_id,
        "jugadores_ids": cinco_alumnos_ids,
        "capitan_id": manager_id,
    })

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_fichar_dos_veces_reemplaza_la_plantilla_en_vez_de_duplicarla(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids, profesor_id
):
    manager_id = cinco_alumnos_ids[0]
    primer_capitan = cinco_alumnos_ids[0]
    segundo_capitan = cinco_alumnos_ids[1]
    await login_como_alumno(cliente, manager_id)

    primera = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": primer_capitan,
    })
    segunda = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": segundo_capitan,
    })

    assert primera.status_code == 201 and segunda.status_code == 201
    assert primera.json()["id"] == segunda.json()["id"]  # misma plantilla, no una nueva
    assert segunda.json()["capitan_id"] == segundo_capitan

    await login_como_profesor(cliente, profesor_id)
    listado = await cliente.get(f"/plantillas/jornada/{jornada_abierta_id}")
    assert len(listado.json()) == 1


@pytest.mark.asyncio
async def test_heredar_plantilla_anterior_cuando_no_se_ficho_a_tiempo(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids, profesor_id
):
    manager_id = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_id)
    await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id,
    })

    # Jornada "siguiente", en la que el manager no llega a fichar a tiempo.
    pool = get_pool()
    ahora = datetime.now()
    await jornadas_repository.crear_lote(pool, clase_id, [{
        "numero": 100, "fecha_inicio": ahora.date(), "fecha_fin": ahora.date(),
        "apertura_fichajes": ahora - timedelta(hours=2), "cierre_fichajes": ahora - timedelta(hours=1),
    }])
    jornadas = await jornadas_repository.listar_por_clase(pool, clase_id)
    jornada_siguiente_id = next(j["id"] for j in jornadas if j["numero"] == 100)

    await login_como_profesor(cliente, profesor_id)
    respuesta = await cliente.post(
        "/plantillas/heredar",
        params={"jornada_actual_id": jornada_siguiente_id,
                "jornada_anterior_id": jornada_abierta_id, "manager_id": manager_id},
    )

    assert respuesta.status_code == 200
    heredada = respuesta.json()
    assert heredada["generada_automaticamente"] is True
    assert heredada["manager_id"] == manager_id
    assert sorted(j["jugador_id"] for j in heredada["jugadores"]) == sorted(cinco_alumnos_ids)


@pytest.mark.asyncio
async def test_heredar_sin_plantilla_previa_no_hace_nada(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    respuesta = await cliente.post(
        "/plantillas/heredar",
        params={"jornada_actual_id": jornada_abierta_id,
                "jornada_anterior_id": jornada_abierta_id, "manager_id": cinco_alumnos_ids[0]},
    )

    assert respuesta.status_code == 200
    assert respuesta.json() is None


@pytest.mark.asyncio
async def test_un_profesor_no_puede_fichar_plantillas(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    respuesta = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": cinco_alumnos_ids[0],
    })

    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_un_alumno_no_puede_ver_todas_las_plantillas_de_la_jornada(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids
):
    await login_como_alumno(cliente, cinco_alumnos_ids[0])

    respuesta = await cliente.get(f"/plantillas/jornada/{jornada_abierta_id}")

    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_un_alumno_puede_ver_su_propia_plantilla_pero_no_la_de_otro(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids
):
    manager_a, manager_b = cinco_alumnos_ids[0], cinco_alumnos_ids[1]
    await login_como_alumno(cliente, manager_a)
    await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_a,
    })

    propia = await cliente.get(f"/plantillas/jornada/{jornada_abierta_id}/manager/{manager_a}")
    ajena = await cliente.get(f"/plantillas/jornada/{jornada_abierta_id}/manager/{manager_b}")

    assert propia.status_code == 200 and propia.json() is not None
    assert ajena.status_code == 403


@pytest.mark.asyncio
async def test_requiere_sesion(cliente):
    respuesta = await cliente.get("/plantillas/jornada/1")
    assert respuesta.status_code == 401
