"""Endpoints del módulo alumnos: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.alumnos import service
from modules.alumnos.schemas import AlumnoCreate, AlumnoOut
from modules.alumnos.service import UsernameDuplicadoError
from modules.clases import service as clases_service

router = APIRouter(prefix="/alumnos", tags=["alumnos"])


@router.post("", response_model=AlumnoOut, status_code=status.HTTP_201_CREATED)
async def api_crear_alumno(clase_id: int, datos: AlumnoCreate, pool: asyncmy.Pool = Depends(get_pool)):
    clase = await clases_service.obtener_clase(pool, clase_id)
    if clase is None:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    try:
        alumno_id = await service.crear_alumno(
            pool, clase_id, datos.nombre, datos.username, datos.password,
            clase["valor_inicial_jugador"],
        )
    except UsernameDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return await service.obtener_alumno(pool, alumno_id)


@router.get("", response_model=list[AlumnoOut])
async def api_listar_alumnos(clase_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_alumnos(pool, clase_id)


@router.get("/vista/listado", response_class=HTMLResponse)
async def vista_listado_alumnos(request: Request, clase_id: int,
                                 pool: asyncmy.Pool = Depends(get_pool)):
    alumnos = await service.listar_alumnos(pool, clase_id)
    return templates.TemplateResponse(
        request, "alumnos/listado.html", {"alumnos": alumnos, "clase_id": clase_id}
    )
