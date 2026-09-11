"""Fixtures compartidas por las pruebas de integración.

Todas ejercitan la app real (lifespan real -> pool de MySQL real) contra la
base de datos del propio docker-compose de desarrollo.
"""
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.database import get_pool
from main import app


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
