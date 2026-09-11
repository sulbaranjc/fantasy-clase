"""Lógica de negocio del módulo catalogo_puntos."""
import asyncmy
from asyncmy.errors import IntegrityError

from modules.catalogo_puntos import repository
from modules.catalogo_puntos.schemas import CatalogoPuntoCreate, CatalogoPuntoUpdate


class NombreDuplicadoError(Exception):
    """Ya existe un tipo de evento con ese nombre en la misma clase.

    Vive en `service.py`, no en `repository.py`, para que el router pueda
    traducirla a un código HTTP sin que ninguna capa dependa de los
    detalles del driver de MySQL salvo esta, que sí necesita capturarlos.
    """


async def crear_evento(pool: asyncmy.Pool, clase_id: int, datos: CatalogoPuntoCreate) -> int:
    try:
        return await repository.crear(pool, clase_id, datos.nombre, datos.puntos)
    except IntegrityError as exc:
        raise NombreDuplicadoError(
            f"Ya existe un evento llamado «{datos.nombre}» en esta clase."
        ) from exc


async def listar_eventos(pool: asyncmy.Pool, clase_id: int, solo_activos: bool = False) -> list[dict]:
    return await repository.listar_por_clase(pool, clase_id, solo_activos)


async def obtener_evento(pool: asyncmy.Pool, catalogo_punto_id: int) -> dict | None:
    return await repository.obtener_por_id(pool, catalogo_punto_id)


async def actualizar_evento(pool: asyncmy.Pool, catalogo_punto_id: int,
                             datos: CatalogoPuntoUpdate) -> None:
    try:
        await repository.actualizar(pool, catalogo_punto_id, datos.nombre, datos.puntos, datos.activo)
    except IntegrityError as exc:
        raise NombreDuplicadoError(
            f"Ya existe un evento llamado «{datos.nombre}» en esta clase."
        ) from exc
