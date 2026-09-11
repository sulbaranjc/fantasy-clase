"""Pruebas de integración del módulo jornadas contra MySQL real."""
import pytest


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
async def test_generar_calendario_de_una_clase_inexistente_devuelve_404(cliente):
    respuesta = await cliente.post("/jornadas/generar", params={"clase_id": 999999})
    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_obtener_jornada_inexistente_devuelve_404(cliente):
    respuesta = await cliente.get("/jornadas/999999")
    assert respuesta.status_code == 404
