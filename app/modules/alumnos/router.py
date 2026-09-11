"""Endpoints del módulo alumnos: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.alumnos import service
from modules.alumnos.schemas import AlumnoOut

router = APIRouter(prefix="/alumnos", tags=["alumnos"])


@router.get("", response_model=list[AlumnoOut])
async def api_listar_alumnos(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_alumnos(pool, clase_id)


@router.get("/vista", response_class=HTMLResponse)
async def vista_listado_alumnos(request: Request, clase_id: int,
                                 pool: asyncmy.Pool = Depends(get_pool)):
    alumnos = await service.listar_alumnos(pool, clase_id)
    return templates.TemplateResponse(
        request, "alumnos/listado.html", {"alumnos": alumnos, "clase_id": clase_id}
    )
