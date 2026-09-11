"""Endpoints del módulo plantillas: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.alumnos import service as alumnos_service
from modules.clases import service as clases_service
from modules.plantillas import service
from modules.plantillas.schemas import PlantillaCreate, PlantillaOut
from modules.plantillas.service import (
    AlumnoInvalidoError,
    FueraDeVentanaError,
    JornadaInvalidaError,
    PresupuestoExcedidoError,
)

router = APIRouter(prefix="/plantillas", tags=["plantillas"])

_ERRORES_DE_NEGOCIO = (AlumnoInvalidoError, JornadaInvalidaError, PresupuestoExcedidoError, FueraDeVentanaError)


@router.post("", response_model=PlantillaOut, status_code=status.HTTP_201_CREATED)
async def api_fichar_plantilla(clase_id: int, datos: PlantillaCreate, pool: asyncmy.Pool = Depends(get_pool)):
    try:
        plantilla_id = await service.fichar_plantilla(pool, clase_id, datos)
    except _ERRORES_DE_NEGOCIO as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return await service.obtener_plantilla_con_jugadores(pool, plantilla_id)


@router.post("/heredar", response_model=PlantillaOut | None)
async def api_heredar_plantilla(jornada_actual_id: int, jornada_anterior_id: int, manager_id: int,
                                 pool: asyncmy.Pool = Depends(get_pool)):
    plantilla_id = await service.heredar_plantilla_anterior(
        pool, jornada_actual_id, jornada_anterior_id, manager_id
    )
    if plantilla_id is None:
        return None
    return await service.obtener_plantilla_con_jugadores(pool, plantilla_id)


@router.get("/{plantilla_id}", response_model=PlantillaOut)
async def api_obtener_plantilla(plantilla_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    plantilla = await service.obtener_plantilla_con_jugadores(pool, plantilla_id)
    if plantilla is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return plantilla


@router.get("/jornada/{jornada_id}", response_model=list[PlantillaOut])
async def api_listar_plantillas_de_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_plantillas_de_jornada(pool, jornada_id)


@router.get("/jornada/{jornada_id}/manager/{manager_id}", response_model=PlantillaOut | None)
async def api_obtener_plantilla_de_manager(jornada_id: int, manager_id: int,
                                            pool: asyncmy.Pool = Depends(get_pool)):
    return await service.obtener_plantilla_de_manager(pool, jornada_id, manager_id)


@router.get("/vista/fichar", response_class=HTMLResponse)
async def vista_fichar_plantilla(request: Request, clase_id: int, jornada_id: int, manager_id: int,
                                  pool: asyncmy.Pool = Depends(get_pool)):
    alumnos = await alumnos_service.listar_alumnos(pool, clase_id)
    clase = await clases_service.obtener_clase(pool, clase_id)
    plantilla_actual = await service.obtener_plantilla_de_manager(pool, jornada_id, manager_id)
    jugadores_actuales = {j["jugador_id"] for j in plantilla_actual["jugadores"]} if plantilla_actual else set()
    capitan_actual = plantilla_actual["capitan_id"] if plantilla_actual else None

    return templates.TemplateResponse(
        request, "plantillas/fichar.html",
        {
            "alumnos": alumnos, "clase_id": clase_id, "jornada_id": jornada_id,
            "manager_id": manager_id, "jugadores_actuales": jugadores_actuales,
            "capitan_actual": capitan_actual, "presupuesto_total": clase["presupuesto_manager"],
        },
    )
