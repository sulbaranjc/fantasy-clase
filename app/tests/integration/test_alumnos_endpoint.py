"""Prueba de integración: ejercita el endpoint real de la API contra una
base de datos MySQL real (la del propio docker-compose de desarrollo),
verificando el flujo completo petición -> servicio -> base de datos.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_listar_alumnos_de_una_clase_inexistente_devuelve_lista_vacia():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            respuesta = await client.get("/alumnos", params={"clase_id": 999999})

    assert respuesta.status_code == 200
    assert respuesta.json() == []


@pytest.mark.asyncio
async def test_salud_confirma_conexion_a_base_de_datos():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            respuesta = await client.get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "base_de_datos": "conectada"}
