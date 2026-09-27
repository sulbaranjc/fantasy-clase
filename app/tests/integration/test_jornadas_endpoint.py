"""Pruebas de integración del módulo jornadas contra MySQL real."""
from datetime import datetime

import pytest

from .conftest import login_como_alumno


@pytest.mark.asyncio
async def test_generar_calendario_crea_12_jornadas(cliente, clase_id):
    # La fixture `clase_id` crea una clase con las mismas fechas que la
    # temporada real de "Fantasy_Clase.xlsx" (21/09/2026 - 05/03/2027).
    respuesta = await cliente.post("/jornadas/generar", params={"clase_id": clase_id})

    assert respuesta.status_code == 201
    jornadas = respuesta.json()
    assert len(jornadas) == 12
    assert jornadas[0]["numero"] == 1
    assert jornadas[-1]["numero"] == 12
    assert jornadas[-1]["fecha_fin"] == "2027-03-05"

    respuesta_listado = await cliente.get("/jornadas", params={"clase_id": clase_id})
    assert respuesta_listado.status_code == 200
    assert len(respuesta_listado.json()) == 12


@pytest.mark.asyncio
async def test_no_permite_generar_el_calendario_dos_veces(cliente, clase_id):
    primera = await cliente.post("/jornadas/generar", params={"clase_id": clase_id})
    assert primera.status_code == 201

    segunda = await cliente.post("/jornadas/generar", params={"clase_id": clase_id})
    assert segunda.status_code == 409


@pytest.mark.asyncio
async def test_generar_calendario_de_una_clase_inexistente_devuelve_404(cliente, profesor_id):
    respuesta = await cliente.post("/jornadas/generar", params={"clase_id": 999999})
    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_obtener_jornada_inexistente_devuelve_404(cliente, profesor_id):
    respuesta = await cliente.get("/jornadas/999999")
    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_un_alumno_puede_listar_las_jornadas_de_su_clase(cliente, clase_id, alumno_id):
    await cliente.post("/jornadas/generar", params={"clase_id": clase_id})
    await login_como_alumno(cliente, alumno_id)

    respuesta = await cliente.get("/jornadas", params={"clase_id": clase_id})

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 12


@pytest.mark.asyncio
async def test_un_alumno_no_puede_generar_el_calendario(cliente, clase_id, alumno_id):
    await login_como_alumno(cliente, alumno_id)

    respuesta = await cliente.post("/jornadas/generar", params={"clase_id": clase_id})

    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_abrir_fichajes_ahora_fuerza_la_ventana_abierta(cliente, clase_id, jornada_id, cinco_alumnos_ids):
    # `jornada_id` usa el calendario real (temporada 2026/2027): su ventana
    # calculada todavía no ha llegado en el momento de correr las pruebas.
    respuesta = await cliente.post(f"/jornadas/{jornada_id}/abrir-fichajes")

    assert respuesta.status_code == 200
    jornada = respuesta.json()
    apertura = datetime.fromisoformat(jornada["apertura_fichajes"])
    cierre = datetime.fromisoformat(jornada["cierre_fichajes"])
    assert abs((apertura - datetime.now()).total_seconds()) < 10
    assert cierre > apertura

    # Ahora sí se puede fichar: la ventana quedó forzada al instante actual.
    manager_id = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_id)
    fichaje = await cliente.post("/plantillas", json={
        "jornada_id": jornada_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id,
    })
    assert fichaje.status_code == 201


@pytest.mark.asyncio
async def test_cerrar_fichajes_ahora_impide_fichar(cliente, clase_id, jornada_abierta_id, cinco_alumnos_ids):
    respuesta = await cliente.post(f"/jornadas/{jornada_abierta_id}/cerrar-fichajes")

    assert respuesta.status_code == 200
    cierre = datetime.fromisoformat(respuesta.json()["cierre_fichajes"])
    assert cierre <= datetime.now()

    manager_id = cinco_alumnos_ids[0]
    await login_como_alumno(cliente, manager_id)
    fichaje = await cliente.post("/plantillas", json={
        "jornada_id": jornada_abierta_id, "jugadores_ids": cinco_alumnos_ids, "capitan_id": manager_id,
    })
    assert fichaje.status_code == 422


@pytest.mark.asyncio
async def test_un_alumno_no_puede_abrir_ni_cerrar_fichajes(cliente, clase_id, jornada_id, alumno_id):
    await login_como_alumno(cliente, alumno_id)

    abrir = await cliente.post(f"/jornadas/{jornada_id}/abrir-fichajes")
    cerrar = await cliente.post(f"/jornadas/{jornada_id}/cerrar-fichajes")

    assert abrir.status_code == 403
    assert cerrar.status_code == 403


@pytest.mark.asyncio
async def test_requiere_sesion(cliente):
    respuesta = await cliente.get("/jornadas", params={"clase_id": 1})
    assert respuesta.status_code == 401
