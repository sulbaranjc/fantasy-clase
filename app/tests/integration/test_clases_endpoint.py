"""Pruebas de integración del módulo clases contra MySQL real.

Todos los endpoints requieren una sesión de profesor; la fixture
`profesor_id` ya deja al `cliente` autenticado como ese profesor.
"""
from datetime import date

import pytest

from core.database import get_pool
from core.security import hash_password
from modules.clases import repository as clases_repository
from modules.profesores import repository as profesores_repository


@pytest.mark.asyncio
async def test_crear_clase_y_recuperarla(cliente, profesor_id):
    payload = {
        "nombre": "1º ESO A — curso 2026/2027",
        "fecha_inicio": "2026-09-21",
        "fecha_fin": "2027-03-05",
        "presupuesto_manager": 120,
    }

    respuesta_creacion = await cliente.post("/clases", json=payload)
    assert respuesta_creacion.status_code == 201
    clase_creada = respuesta_creacion.json()
    assert clase_creada["nombre"] == payload["nombre"]
    assert clase_creada["profesor_id"] == profesor_id
    # Valores por defecto de la regla de negocio, no enviados en el payload.
    assert clase_creada["valor_inicial_jugador"] == 20
    assert clase_creada["valor_minimo_jugador"] == 10

    respuesta_detalle = await cliente.get(f"/clases/{clase_creada['id']}")
    assert respuesta_detalle.status_code == 200
    assert respuesta_detalle.json() == clase_creada

    respuesta_listado = await cliente.get("/clases")
    assert respuesta_listado.status_code == 200
    ids_listados = [c["id"] for c in respuesta_listado.json()]
    assert clase_creada["id"] in ids_listados


@pytest.mark.asyncio
async def test_rechaza_fecha_fin_anterior_a_fecha_inicio(cliente, profesor_id):
    payload = {
        "nombre": "Clase con fechas inválidas",
        "fecha_inicio": "2026-09-21",
        "fecha_fin": "2026-01-01",
    }

    respuesta = await cliente.post("/clases", json=payload)

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_obtener_clase_inexistente_devuelve_404(cliente, profesor_id):
    respuesta = await cliente.get("/clases/999999")

    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_no_permite_ver_una_clase_de_otro_profesor(cliente, clase_id):
    # `clase_id` pertenece al profesor con el que el `cliente` inició
    # sesión. Un segundo profesor no debe poder verla.
    pool = get_pool()
    otro_username = f"otro_profesor_test_{clase_id}"
    otro_id = await profesores_repository.crear(pool, "Otro profesor", otro_username, hash_password("otra-clave-1234"))
    login = await cliente.post("/auth/profesor/login", json={"username": otro_username, "password": "otra-clave-1234"})
    assert login.status_code == 200

    try:
        respuesta = await cliente.get(f"/clases/{clase_id}")
        assert respuesta.status_code == 404
    finally:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM profesores WHERE id = %s", (otro_id,))


@pytest.mark.asyncio
async def test_actualizar_presupuesto_y_limite_de_equipos(cliente, clase_id):
    respuesta = await cliente.put(
        f"/clases/{clase_id}",
        json={"presupuesto_manager": 150, "limite_equipos_por_jugador": 4},
    )

    assert respuesta.status_code == 200
    clase = respuesta.json()
    assert clase["presupuesto_manager"] == 150
    assert clase["limite_equipos_por_jugador"] == 4

    # Persiste de verdad, no solo en la respuesta.
    respuesta_detalle = await cliente.get(f"/clases/{clase_id}")
    assert respuesta_detalle.json()["presupuesto_manager"] == 150
    assert respuesta_detalle.json()["limite_equipos_por_jugador"] == 4


@pytest.mark.asyncio
async def test_no_permite_editar_una_clase_de_otro_profesor(cliente, clase_id):
    pool = get_pool()
    otro_username = f"otro_profesor_edit_{clase_id}"
    otro_id = await profesores_repository.crear(pool, "Otro profesor", otro_username, hash_password("otra-clave-1234"))
    login = await cliente.post("/auth/profesor/login", json={"username": otro_username, "password": "otra-clave-1234"})
    assert login.status_code == 200

    try:
        respuesta = await cliente.put(
            f"/clases/{clase_id}",
            json={"presupuesto_manager": 999, "limite_equipos_por_jugador": 1},
        )
        assert respuesta.status_code == 404
    finally:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM profesores WHERE id = %s", (otro_id,))


@pytest.mark.asyncio
async def test_requiere_sesion_de_profesor(cliente):
    respuesta = await cliente.post("/clases", json={
        "nombre": "Sin sesión", "fecha_inicio": "2026-09-21", "fecha_fin": "2027-03-05",
    })

    assert respuesta.status_code == 401
