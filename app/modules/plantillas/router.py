"""Endpoints del módulo plantillas: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí.

Fichar es siempre en nombre propio: `clase_id` y `manager_id` se toman de
la sesión del alumno autenticado, nunca del payload ni de la query."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.alumnos import service as alumnos_service
from modules.auth.dependencies import obtener_usuario_actual, requiere_alumno, requiere_profesor
from modules.auth.schemas import UsuarioAutenticado
from modules.clases import service as clases_service
from modules.jornadas import service as jornadas_service
from modules.plantillas import service
from modules.plantillas.schemas import PlantillaCreate, PlantillaOut
from modules.plantillas.service import (
    AlumnoInvalidoError,
    FueraDeVentanaError,
    JornadaInvalidaError,
    ManagerDebeIncluirseError,
    PresupuestoExcedidoError,
)

router = APIRouter(prefix="/plantillas", tags=["plantillas"])

_ERRORES_DE_NEGOCIO = (
    AlumnoInvalidoError, JornadaInvalidaError, PresupuestoExcedidoError,
    FueraDeVentanaError, ManagerDebeIncluirseError,
)


async def _verificar_jornada_del_profesor(pool: asyncmy.Pool, jornada_id: int, profesor_id: int) -> dict:
    jornada = await jornadas_service.obtener_jornada(pool, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    if await clases_service.obtener_clase_del_profesor(pool, jornada["clase_id"], profesor_id) is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    return jornada


@router.post("", response_model=PlantillaOut, status_code=status.HTTP_201_CREATED)
async def api_fichar_plantilla(datos: PlantillaCreate, pool: asyncmy.Pool = Depends(get_pool),
                                alumno: UsuarioAutenticado = Depends(requiere_alumno)):
    try:
        plantilla_id = await service.fichar_plantilla(pool, alumno.clase_id, alumno.id, datos)
    except _ERRORES_DE_NEGOCIO as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return await service.obtener_plantilla_con_jugadores(pool, plantilla_id)


@router.post("/heredar", response_model=PlantillaOut | None)
async def api_heredar_plantilla(jornada_actual_id: int, jornada_anterior_id: int, manager_id: int,
                                 pool: asyncmy.Pool = Depends(get_pool),
                                 profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    await _verificar_jornada_del_profesor(pool, jornada_actual_id, profesor.id)

    plantilla_id = await service.heredar_plantilla_anterior(
        pool, jornada_actual_id, jornada_anterior_id, manager_id
    )
    if plantilla_id is None:
        return None
    return await service.obtener_plantilla_con_jugadores(pool, plantilla_id)


@router.get("/jornada/{jornada_id}", response_model=list[PlantillaOut])
async def api_listar_plantillas_de_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                            profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    await _verificar_jornada_del_profesor(pool, jornada_id, profesor.id)
    return await service.listar_plantillas_de_jornada(pool, jornada_id)


@router.get("/jornada/{jornada_id}/manager/{manager_id}", response_model=PlantillaOut | None)
async def api_obtener_plantilla_de_manager(jornada_id: int, manager_id: int,
                                            pool: asyncmy.Pool = Depends(get_pool),
                                            usuario: UsuarioAutenticado = Depends(obtener_usuario_actual)):
    jornada = await jornadas_service.obtener_jornada(pool, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")

    if usuario.tipo == "alumno":
        if usuario.id != manager_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes ver tu propia plantilla.")
    elif await clases_service.obtener_clase_del_profesor(pool, jornada["clase_id"], usuario.id) is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")

    return await service.obtener_plantilla_de_manager(pool, jornada_id, manager_id)


@router.get("/{plantilla_id}", response_model=PlantillaOut)
async def api_obtener_plantilla(plantilla_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                 usuario: UsuarioAutenticado = Depends(obtener_usuario_actual)):
    plantilla = await service.obtener_plantilla_con_jugadores(pool, plantilla_id)
    if plantilla is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    if usuario.tipo == "alumno":
        if usuario.id != plantilla["manager_id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes ver tu propia plantilla.")
    else:
        jornada = await jornadas_service.obtener_jornada(pool, plantilla["jornada_id"])
        if await clases_service.obtener_clase_del_profesor(pool, jornada["clase_id"], usuario.id) is None:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    return plantilla


@router.get("/vista/fichar", response_class=HTMLResponse)
async def vista_fichar_plantilla(request: Request, jornada_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                  alumno: UsuarioAutenticado = Depends(requiere_alumno)):
    alumnos = await alumnos_service.listar_alumnos(pool, alumno.clase_id)
    clase = await clases_service.obtener_clase(pool, alumno.clase_id)
    plantilla_actual = await service.obtener_plantilla_de_manager(pool, jornada_id, alumno.id)
    jugadores_actuales = {j["jugador_id"] for j in plantilla_actual["jugadores"]} if plantilla_actual else set()
    capitan_actual = plantilla_actual["capitan_id"] if plantilla_actual else None

    return templates.TemplateResponse(
        request, "plantillas/fichar.html",
        {
            "alumnos": alumnos, "jornada_id": jornada_id, "manager_id": alumno.id,
            "jugadores_actuales": jugadores_actuales, "capitan_actual": capitan_actual,
            "presupuesto_total": clase["presupuesto_manager"],
        },
    )
