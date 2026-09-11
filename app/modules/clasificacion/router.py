"""Endpoints del módulo clasificacion: reciben la petición HTTP y delegan
en `service`. Sin lógica de negocio aquí. Todo es de solo lectura."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.clasificacion import service
from modules.clasificacion.schemas import (
    ClasificacionGeneralOut,
    ClasificacionJornadaOut,
    ValidacionSeleccionOut,
)

router = APIRouter(prefix="/clasificacion", tags=["clasificacion"])


@router.get("/jornada/{jornada_id}", response_model=list[ClasificacionJornadaOut])
async def api_clasificacion_de_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.clasificacion_de_jornada(pool, jornada_id)


@router.get("/general", response_model=list[ClasificacionGeneralOut])
async def api_clasificacion_general(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.clasificacion_general(pool, clase_id)


@router.get("/podio", response_model=list[ClasificacionGeneralOut])
async def api_podio(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.podio(pool, clase_id)


@router.get("/validacion-seleccion", response_model=list[ValidacionSeleccionOut])
async def api_validar_seleccion(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.validar_seleccion_completa(pool, clase_id)


@router.get("/vista/general", response_class=HTMLResponse)
async def vista_clasificacion_general(request: Request, clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    clasificacion = await service.clasificacion_general(pool, clase_id)
    return templates.TemplateResponse(
        request, "clasificacion/general.html", {"clasificacion": clasificacion, "clase_id": clase_id}
    )


@router.get("/vista/validacion-seleccion", response_class=HTMLResponse)
async def vista_validacion_seleccion(request: Request, clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    validacion = await service.validar_seleccion_completa(pool, clase_id)
    return templates.TemplateResponse(
        request, "clasificacion/validacion_seleccion.html", {"validacion": validacion, "clase_id": clase_id}
    )
