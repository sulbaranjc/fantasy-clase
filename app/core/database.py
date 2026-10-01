"""Pool de conexión asíncrono a MySQL.

Sin ORM por decisión del proyecto: los módulos escriben su propio SQL contra
este pool. `get_pool()` se usa como dependencia de FastAPI para inyectar una
conexión en cada request sin acoplar los servicios al framework.
"""
import asyncio
import logging

import asyncmy

from core.config import get_settings

logger = logging.getLogger("fantasy_clase")

_pool: asyncmy.Pool | None = None

_INTENTOS_CONEXION_MAXIMOS = 10
_ESPERA_ENTRE_INTENTOS_SEGUNDOS = 2


async def init_pool() -> asyncmy.Pool:
    """Crea el pool una vez, al arrancar la aplicación (evento startup).

    Reintenta varias veces antes de rendirse: en el primer arranque del
    stack (o tras cualquier reinicio), MySQL 8.x hace un reinicio interno
    propio justo después de inicializar su datadir, y si la app intenta
    conectar en esa ventana el primer intento falla. Sin reintentos, el
    lifespan de FastAPI aborta y el proceso queda sirviendo 502 de forma
    indefinida aunque MySQL esté perfectamente sano segundos después.
    """
    global _pool
    settings = get_settings()
    ultimo_error: Exception | None = None
    for intento in range(1, _INTENTOS_CONEXION_MAXIMOS + 1):
        try:
            _pool = await asyncmy.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                db=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                autocommit=True,
                minsize=1,
                maxsize=10,
            )
            return _pool
        except asyncmy.errors.OperationalError as exc:
            ultimo_error = exc
            if intento < _INTENTOS_CONEXION_MAXIMOS:
                logger.warning(
                    "No se pudo conectar a MySQL (intento %d/%d), reintentando en %ds: %s",
                    intento, _INTENTOS_CONEXION_MAXIMOS, _ESPERA_ENTRE_INTENTOS_SEGUNDOS, exc,
                )
                await asyncio.sleep(_ESPERA_ENTRE_INTENTOS_SEGUNDOS)
    raise ultimo_error


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


def get_pool() -> asyncmy.Pool:
    if _pool is None:
        raise RuntimeError("El pool de base de datos no está inicializado todavía.")
    return _pool
