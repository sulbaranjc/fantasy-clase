"""Endpoints del módulo jornadas: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.jornadas import service
from modules.jornadas.schemas import JornadaOut
from modules.jornadas.service import CalendarioYaGeneradoError, ClaseInexistenteError

router = APIRouter(prefix="/jornadas", tags=["jornadas"])


@router.post("/generar", response_model=list[JornadaOut], status_code=status.HTTP_201_CREATED)
async def api_generar_calendario(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    try:
        return await service.generar_y_guardar_calendario(pool, clase_id)
    except ClaseInexistenteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CalendarioYaGeneradoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[JornadaOut])
async def api_listar_jornadas(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_jornadas(pool, clase_id)


@router.get("/{jornada_id}", response_model=JornadaOut)
async def api_obtener_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    jornada = await service.obtener_jornada(pool, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    return jornada


@router.get("/vista/listado", response_class=HTMLResponse)
async def vista_listado_jornadas(request: Request, clase_id: int,
                                  pool: asyncmy.Pool = Depends(get_pool)):
    jornadas = await service.listar_jornadas(pool, clase_id)
    return templates.TemplateResponse(
        request, "jornadas/listado.html", {"jornadas": jornadas, "clase_id": clase_id}
    )
