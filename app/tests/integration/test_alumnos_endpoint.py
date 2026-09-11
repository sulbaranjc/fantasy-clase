"""Prueba de integración: ejercita el endpoint real de la API contra una
base de datos MySQL real (la del propio docker-compose de desarrollo),
verificando el flujo completo petición -> servicio -> base de datos.
"""
from datetime import date

import pytest

from modules.clases import repository as clases_repository


@pytest.mark.asyncio
async def test_listar_alumnos_de_una_clase_inexistente_devuelve_lista_vacia(cliente):
    respuesta = await cliente.get("/alumnos", params={"clase_id": 999999})

    assert respuesta.status_code == 200
    assert respuesta.json() == []


@pytest.mark.asyncio
async def test_salud_confirma_conexion_a_base_de_datos(cliente):
    respuesta = await cliente.get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "base_de_datos": "conectada"}


@pytest.mark.asyncio
async def test_crear_alumno_hereda_el_valor_inicial_de_la_clase(cliente, clase_id):
    payload = {"nombre": "María López", "username": "maria.lopez", "password": "clave1234"}

    respuesta = await cliente.post("/alumnos", params={"clase_id": clase_id}, json=payload)

    assert respuesta.status_code == 201
    alumno = respuesta.json()
    assert alumno["nombre"] == "María López"
    assert alumno["username"] == "maria.lopez"
    assert alumno["valor_actual"] == 20  # valor_inicial_jugador por defecto de la clase
    assert "password" not in alumno and "password_hash" not in alumno


@pytest.mark.asyncio
async def test_no_permite_usuarios_duplicados_en_la_misma_clase(cliente, clase_id):
    payload = {"nombre": "Alumno 1", "username": "duplicado", "password": "clave1234"}

    primera = await cliente.post("/alumnos", params={"clase_id": clase_id}, json=payload)
    assert primera.status_code == 201

    segunda = await cliente.post(
        "/alumnos", params={"clase_id": clase_id},
        json={"nombre": "Otro alumno", "username": "duplicado", "password": "clave5678"},
    )
    assert segunda.status_code == 409


@pytest.mark.asyncio
async def test_no_permite_usuarios_duplicados_entre_clases_distintas(cliente, clase_id, profesor_id):
    # El username es único entre TODAS las clases del profesor (migración
    # 005): el login de alumno no pide seleccionar de qué clase es.
    from core.database import get_pool

    pool = get_pool()
    otra_clase_id = await clases_repository.crear(
        pool, profesor_id=profesor_id, nombre="Otra clase", fecha_inicio=date(2026, 9, 21),
        fecha_fin=date(2027, 3, 5), duracion_jornada_dias=14, ventana_fichaje_horas=24,
        valor_inicial_jugador=20, valor_minimo_jugador=10, factor_recalculo_valor=0.10,
        presupuesto_manager=120,
    )

    primera = await cliente.post(
        "/alumnos", params={"clase_id": clase_id},
        json={"nombre": "Alumno 1", "username": "compartido", "password": "clave1234"},
    )
    assert primera.status_code == 201

    segunda = await cliente.post(
        "/alumnos", params={"clase_id": otra_clase_id},
        json={"nombre": "Alumno de otra clase", "username": "compartido", "password": "clave5678"},
    )
    assert segunda.status_code == 409


@pytest.mark.asyncio
async def test_crear_alumno_en_clase_inexistente_devuelve_404(cliente):
    payload = {"nombre": "Alumno", "username": "alumno_x", "password": "clave1234"}

    respuesta = await cliente.post("/alumnos", params={"clase_id": 999999}, json=payload)

    assert respuesta.status_code == 404
