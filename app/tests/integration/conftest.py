"""Fixtures compartidas por las pruebas de integración.

Todas ejercitan la app real (lifespan real -> pool de MySQL real) contra la
base de datos del propio docker-compose de desarrollo.
"""
import uuid
from datetime import date

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.database import get_pool
from core.security import hash_password
from main import app
from modules.alumnos import repository as alumnos_repository
from modules.catalogo_puntos import repository as catalogo_repository
from modules.clases import repository as clases_repository
from modules.jornadas import service as jornadas_service


@pytest_asyncio.fixture
async def cliente():
    """Cliente HTTP async contra la app, con su lifespan (pool de MySQL)
    activo durante todo el test."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest_asyncio.fixture
async def profesor_id(cliente):
    """Inserta un profesor de prueba directamente en base de datos.

    El módulo `auth` (que expondrá el alta real de profesores) todavía no
    existe; mientras tanto, los módulos que dependen de un profesor válido
    (como `clases`) usan esta fixture. Se limpia al terminar el test; la
    cascada de la base de datos borra también las clases que haya creado.
    """
    pool = get_pool()
    username = f"profesor_test_{uuid.uuid4().hex[:12]}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO profesores (nombre, username, password_hash) VALUES (%s, %s, %s)",
                ("Profesor de prueba", username, "hash-no-usado-en-pruebas"),
            )
            nuevo_id = cur.lastrowid

    yield nuevo_id

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM profesores WHERE id = %s", (nuevo_id,))


@pytest_asyncio.fixture
async def clase_id(profesor_id):
    """Crea una clase de prueba (a través del propio módulo `clases`, no
    con SQL a mano) para los módulos que dependen de una clase existente
    (catalogo_puntos, jornadas, eventos, plantillas...).

    No hace falta limpiarla explícitamente: al borrar el profesor de
    prueba, la cascada de la base de datos se lleva también sus clases.
    """
    pool = get_pool()
    nuevo_id = await clases_repository.crear(
        pool,
        profesor_id=profesor_id,
        nombre="Clase de prueba",
        fecha_inicio=date(2026, 9, 21),
        fecha_fin=date(2027, 3, 5),
        duracion_jornada_dias=14,
        ventana_fichaje_horas=24,
        valor_inicial_jugador=20,
        valor_minimo_jugador=10,
        factor_recalculo_valor=0.10,
        presupuesto_manager=120,
    )
    return nuevo_id


@pytest_asyncio.fixture
async def alumno_id(clase_id):
    """Crea un alumno de prueba en la clase, para los módulos que dependen
    de un alumno existente (eventos, plantillas...)."""
    pool = get_pool()
    username = f"alumno_test_{uuid.uuid4().hex[:12]}"
    return await alumnos_repository.crear(
        pool, clase_id, "Alumno de prueba", username, hash_password("clave-no-usada"), 20
    )


@pytest_asyncio.fixture
async def catalogo_punto_id(clase_id):
    """Crea un tipo de evento de prueba en la clase, para los módulos que
    dependen de una entrada del catálogo de puntos (eventos...)."""
    pool = get_pool()
    return await catalogo_repository.crear(pool, clase_id, "Evento de prueba", 5)


@pytest_asyncio.fixture
async def jornada_id(clase_id):
    """Genera el calendario de la clase de prueba y devuelve el id de su
    primera jornada, para los módulos que dependen de una jornada existente
    (eventos, plantillas...)."""
    pool = get_pool()
    jornadas = await jornadas_service.generar_y_guardar_calendario(pool, clase_id)
    return jornadas[0]["id"]
