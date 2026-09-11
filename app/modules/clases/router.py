"""Endpoints del módulo clases: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí.

`profesor_id` se recibe todavía como parámetro explícito porque el módulo
`auth` (login del profesor) aún no está implementado; cuando exista, estos
endpoints pasarán a tomarlo de la sesión autenticada en vez de la query.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.clases import service
from modules.clases.schemas import ClaseCreate, ClaseOut

router = APIRouter(prefix="/clases", tags=["clases"])


@router.post("", response_model=ClaseOut, status_code=status.HTTP_201_CREATED)
async def api_crear_clase(profesor_id: int, datos: ClaseCreate,
                           pool: asyncmy.Pool = Depends(get_pool)):
    clase_id = await service.crear_clase(pool, profesor_id, datos)
    return await service.obtener_clase(pool, clase_id)


@router.get("", response_model=list[ClaseOut])
async def api_listar_clases(profesor_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_clases_de_profesor(pool, profesor_id)


@router.get("/{clase_id}", response_model=ClaseOut)
async def api_obtener_clase(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    clase = await service.obtener_clase(pool, clase_id)
    if clase is None:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    return clase


@router.get("/vista/listado", response_class=HTMLResponse)
async def vista_listado_clases(request: Request, profesor_id: int,
                                pool: asyncmy.Pool = Depends(get_pool)):
    clases = await service.listar_clases_de_profesor(pool, profesor_id)
    return templates.TemplateResponse(
        request, "clases/listado.html", {"clases": clases, "profesor_id": profesor_id}
    )
