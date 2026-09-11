"""Pruebas de integración del módulo plantillas contra MySQL real."""
from datetime import datetime, timedelta

import pytest

from core.database import get_pool
from modules.alumnos import repository as alumnos_repository
from modules.jornadas import repository as jornadas_repository


@pytest.mark.asyncio
async def test_fichar_plantilla_dentro_de_ventana_y_presupuesto(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    manager_id = cinco_alumnos_ids[0]
    payload = {
        "jornada_id": jornada_abierta_id,
        "manager_id": manager_id,
        "jugadores_ids": cinco_alumnos_ids,
        "capitan_id": manager_id,
    }

    respuesta = await cliente.post("/plantillas", params={"clase_id": clase_id}, json=payload)

    assert respuesta.status_code == 201
    plantilla = respuesta.json()
    assert plantilla["manager_id"] == manager_id
    assert plantilla["capitan_id"] == manager_id
    assert plantilla["generada_automaticamente"] is False
    assert sorted(j["jugador_id"] for j in plantilla["jugadores"]) == sorted(cinco_alumnos_ids)
    assert all(j["valor_al_fichar"] == 20 for j in plantilla["jugadores"])


@pytest.mark.asyncio
async def test_rechaza_plantilla_que_excede_el_presupuesto(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    # Sube el valor de un jugador para que 20*4 + 100 = 180 > 120 (presupuesto por defecto).
    pool = get_pool()
    await alumnos_repository.actualizar_valor(pool, cinco_alumnos_ids[0], 100)

    manager_id = cinco_alumnos_ids[1]
    payload = {
        "jornada_id": jornada_abierta_id,
        "manager_id": manager_id,
        "jugadores_ids": cinco_alumnos_ids,
        "capitan_id": manager_id,
    }

    respuesta = await cliente.post("/plantillas", params={"clase_id": clase_id}, json=payload)

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_rechaza_fichar_fuera_de_la_ventana_de_fichajes(cliente, clase_id, jornada_id, cinco_alumnos_ids):
    # `jornada_id` usa el calendario real (temporada 2026/2027); su ventana
    # de fichajes todavía no ha abierto en el momento de correr las pruebas.
    manager_id = cinco_alumnos_ids[0]
    payload = {
        "jornada_id": jornada_id,
        "manager_id": manager_id,
        "jugadores_ids": cinco_alumnos_ids,
        "capitan_id": manager_id,
    }

    respuesta = await cliente.post("/plantillas", params={"clase_id": clase_id}, json=payload)

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_fichar_dos_veces_reemplaza_la_plantilla_en_vez_de_duplicarla(
    cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids
):
    manager_id = cinco_alumnos_ids[0]
    primer_capitan = cinco_alumnos_ids[0]
    segundo_capitan = cinco_alumnos_ids[1]

    primera = await cliente.post(
        "/plantillas", params={"clase_id": clase_id},
        json={"jornada_id": jornada_abierta_id, "manager_id": manager_id,
              "jugadores_ids": cinco_alumnos_ids, "capitan_id": primer_capitan},
    )
    segunda = await cliente.post(
        "/plantillas", params={"clase_id": clase_id},
        json={"jornada_id": jornada_abierta_id, "manager_id": manager_id,
              "jugadores_ids": cinco_alumnos_ids, "capitan_id": segundo_capitan},
    )

    assert primera.status_code == 201 and segunda.status_code == 201
    assert primera.json()["id"] == segunda.json()["id"]  # misma plantilla, no una nueva
    assert segunda.json()["capitan_id"] == segundo_capitan

    listado = await cliente.get(f"/plantillas/jornada/{jornada_abierta_id}")
    assert len(listado.json()) == 1


@pytest.mark.asyncio
async def test_heredar_plantilla_anterior_cuando_no_se_ficho_a_tiempo(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    manager_id = cinco_alumnos_ids[0]

    await cliente.post(
        "/plantillas", params={"clase_id": clase_id},
        json={"jornada_id": jornada_abierta_id, "manager_id": manager_id,
              "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id},
    )

    # Jornada "siguiente", en la que el manager no llega a fichar a tiempo.
    pool = get_pool()
    ahora = datetime.now()
    await jornadas_repository.crear_lote(pool, clase_id, [{
        "numero": 100, "fecha_inicio": ahora.date(), "fecha_fin": ahora.date(),
        "apertura_fichajes": ahora - timedelta(hours=2), "cierre_fichajes": ahora - timedelta(hours=1),
    }])
    jornadas = await jornadas_repository.listar_por_clase(pool, clase_id)
    jornada_siguiente_id = next(j["id"] for j in jornadas if j["numero"] == 100)

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
