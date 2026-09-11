"""Endpoints del módulo catalogo_puntos: reciben la petición HTTP y
delegan en `service`. Sin lógica de negocio aquí."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.catalogo_puntos import service
from modules.catalogo_puntos.schemas import CatalogoPuntoCreate, CatalogoPuntoOut, CatalogoPuntoUpdate
from modules.catalogo_puntos.service import NombreDuplicadoError

router = APIRouter(prefix="/catalogo-puntos", tags=["catalogo_puntos"])


@router.post("", response_model=CatalogoPuntoOut, status_code=status.HTTP_201_CREATED)
async def api_crear_evento(clase_id: int, datos: CatalogoPuntoCreate,
                            pool: asyncmy.Pool = Depends(get_pool)):
    try:
        evento_id = await service.crear_evento(pool, clase_id, datos)
    except NombreDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return await service.obtener_evento(pool, evento_id)


@router.get("", response_model=list[CatalogoPuntoOut])
async def api_listar_eventos(clase_id: int, solo_activos: bool = False,
                              pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_eventos(pool, clase_id, solo_activos)


@router.get("/{catalogo_punto_id}", response_model=CatalogoPuntoOut)
async def api_obtener_evento(catalogo_punto_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    evento = await service.obtener_evento(pool, catalogo_punto_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")
    return evento


@router.put("/{catalogo_punto_id}", response_model=CatalogoPuntoOut)
async def api_actualizar_evento(catalogo_punto_id: int, datos: CatalogoPuntoUpdate,
                                 pool: asyncmy.Pool = Depends(get_pool)):
    if await service.obtener_evento(pool, catalogo_punto_id) is None:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")
    try:
        await service.actualizar_evento(pool, catalogo_punto_id, datos)
    except NombreDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return await service.obtener_evento(pool, catalogo_punto_id)


@router.get("/vista/listado", response_class=HTMLResponse)
async def vista_listado_eventos(request: Request, clase_id: int,
                                 pool: asyncmy.Pool = Depends(get_pool)):
    eventos = await service.listar_eventos(pool, clase_id)
    return templates.TemplateResponse(
        request, "catalogo_puntos/listado.html", {"eventos": eventos, "clase_id": clase_id}
    )
