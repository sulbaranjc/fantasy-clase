"""Pruebas unitarias de `init_pool`: que reintente ante un fallo transitorio
de conexión a MySQL en vez de rendirse al primer intento.

Único lugar del proyecto que usa mocking (en vez de MySQL real): no hay forma
razonable de reproducir de manera determinista un fallo de conexión transitorio
contra una base de datos real sin ralentizar la suite.
"""
from unittest.mock import AsyncMock, patch

import asyncmy
import pytest

from core import database


@pytest.fixture(autouse=True)
def limpiar_pool():
    yield
    database._pool = None


@pytest.mark.asyncio
async def test_reintenta_tras_un_fallo_transitorio_y_termina_conectando():
    pool_falso = object()
    create_pool = AsyncMock(side_effect=[
        asyncmy.errors.OperationalError(2003, "Can't connect to MySQL server"),
        asyncmy.errors.OperationalError(2003, "Can't connect to MySQL server"),
        pool_falso,
    ])

    with patch("asyncmy.create_pool", create_pool), patch("core.database.asyncio.sleep", AsyncMock()):
        resultado = await database.init_pool()

    assert resultado is pool_falso
    assert create_pool.call_count == 3


@pytest.mark.asyncio
async def test_se_rinde_tras_agotar_los_intentos():
    error_final = asyncmy.errors.OperationalError(2003, "Can't connect to MySQL server")
    create_pool = AsyncMock(side_effect=error_final)

    with patch("asyncmy.create_pool", create_pool), patch("core.database.asyncio.sleep", AsyncMock()):
        with pytest.raises(asyncmy.errors.OperationalError):
            await database.init_pool()

    assert create_pool.call_count == database._INTENTOS_CONEXION_MAXIMOS
