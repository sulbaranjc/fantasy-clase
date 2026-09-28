"""Pruebas de integración del módulo plantillas contra MySQL real.

Fichar exige sesión de alumno (`login_como_alumno`); administrar
(heredar, listar todas las plantillas de una jornada) exige profesor.
"""
import uuid
from datetime import datetime, timedelta

import pytest

from core.database import get_pool
from core.security import hash_password
from modules.alumnos import repository as alumnos_repository
from modules.jornadas import repository as jornadas_repository

from .conftest import PASSWORD_ALUMNOS_PRUEBA, login_como_alumno, login_como_profesor


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
async def test_limite_de_equipos_por_jugador(cliente, clase_id, jornada_abierta_id, profesor_id):
    # Grupos de relleno EXCLUSIVOS por manager, para que el único jugador
    # que se acerca al límite en este test sea `jugador_objetivo`.
    pool = get_pool()

    async def crear_alumno(nombre):
        username = f"limite_test_{uuid.uuid4().hex[:10]}"
        return await alumnos_repository.crear(
            pool, clase_id, nombre, username, hash_password(PASSWORD_ALUMNOS_PRUEBA), 20
        )

    jugador_objetivo = await crear_alumno("Jugador Objetivo")
    manager_1 = await crear_alumno("Manager 1")
    manager_2 = await crear_alumno("Manager 2")
    # manager + jugador_objetivo + 3 de relleno = exactamente 5 (regla de forma de la plantilla).
    relleno_1 = [await crear_alumno(f"Relleno1-{i}") for i in range(3)]
    relleno_2 = [await crear_alumno(f"Relleno2-{i}") for i in range(3)]

    await login_como_profesor(cliente, profesor_id)
    ajuste = await cliente.put(f"/clases/{clase_id}", json={
        "presupuesto_manager": 120, "limite_equipos_por_jugador": 1,
    })
    assert ajuste.status_code == 200

    await login_como_alumno(cliente, manager_1)
    primera = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id,
        "jugadores_ids": [manager_1, jugador_objetivo] + relleno_1,
        "capitan_id": manager_1,
    })
    assert primera.status_code == 201

    # Con el límite en 1, ningún otro manager puede fichar ya al mismo jugador.
    await login_como_alumno(cliente, manager_2)
    segunda = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id,
        "jugadores_ids": [manager_2, jugador_objetivo] + relleno_2,
        "capitan_id": manager_2,
    })
    assert segunda.status_code == 422

    # manager_1 puede volver a guardar SU PROPIA plantilla sin problema:
    # no cuenta contra el límite fichar de nuevo a alguien que ya tenía.
    await login_como_alumno(cliente, manager_1)
    reemplazo = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id,
        "jugadores_ids": [manager_1, jugador_objetivo] + relleno_1,
        "capitan_id": manager_1,
    })
    assert reemplazo.status_code == 201


@pytest.mark.asyncio
async def test_no_puede_repetir_companeros_de_la_jornada_anterior(cliente, clase_id, cinco_alumnos_ids):
    # Petición de Álvaro: forzar rotación, que los alumnos no repitan
    # siempre al mismo grupo de compañeros de una jornada a la siguiente.
    pool = get_pool()
    manager_id = cinco_alumnos_ids[0]
    companeros_anteriores = cinco_alumnos_ids[1:]

    jornada_1_id = await _crear_jornada_abierta(clase_id, 1)
    jornada_2_id = await _crear_jornada_abierta(clase_id, 2)

    async def crear_alumno(nombre):
        username = f"rotacion_test_{uuid.uuid4().hex[:10]}"
        return await alumnos_repository.crear(
            pool, clase_id, nombre, username, hash_password(PASSWORD_ALUMNOS_PRUEBA), 20
        )

    nuevos_companeros = [await crear_alumno(f"Nuevo-{i}") for i in range(4)]

    await login_como_alumno(cliente, manager_id)
    primera = await cliente.post("/plantillas", json={
        "jornada_id": jornada_1_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id,
    })
    assert primera.status_code == 201

    repite_uno = await cliente.post("/plantillas", json={
        "jornada_id": jornada_2_id,
        "jugadores_ids": [manager_id, *nuevos_companeros[:3], companeros_anteriores[0]],
        "capitan_id": manager_id,
    })
    assert repite_uno.status_code == 422

    todos_nuevos = await cliente.post("/plantillas", json={
        "jornada_id": jornada_2_id,
        "jugadores_ids": [manager_id, *nuevos_companeros],
        "capitan_id": manager_id,
    })
    assert todos_nuevos.status_code == 201


@pytest.mark.asyncio
async def test_la_primera_jornada_no_tiene_restriccion_de_rotacion(cliente, clase_id, cinco_alumnos_ids):
    # Sin jornada anterior no hay nada que comparar: nunca debe rechazarse.
    jornada_1_id = await _crear_jornada_abierta(clase_id, 1)
    manager_id = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_id)

    respuesta = await cliente.post("/plantillas", json={
        "jornada_id": jornada_1_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id,
    })

    assert respuesta.status_code == 201


@pytest.mark.asyncio
async def test_requiere_sesion(cliente):
    respuesta = await cliente.get("/plantillas/jornada/1")
    assert respuesta.status_code == 401
