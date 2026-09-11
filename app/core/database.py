"""Pool de conexión asíncrono a MySQL.

Sin ORM por decisión del proyecto: los módulos escriben su propio SQL contra
este pool. `get_pool()` se usa como dependencia de FastAPI para inyectar una
conexión en cada request sin acoplar los servicios al framework.
"""
import asyncmy

from core.config import get_settings

_pool: asyncmy.Pool | None = None


async def init_pool() -> asyncmy.Pool:
    """Crea el pool una vez, al arrancar la aplicación (evento startup)."""
    global _pool
    settings = get_settings()
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
