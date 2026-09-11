"""Endpoints del módulo clasificacion: reciben la petición HTTP y delegan
en `service`. Sin lógica de negocio aquí. Todo es de solo lectura.

La clasificación (por jornada, general, podio) es información compartida
del "juego": la ve el profesor dueño o cualquier alumno de la clase. La
validación de selección es una herramienta de administración, solo para
el profesor.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.auth.dependencies import obtener_usuario_actual
from modules.auth.schemas import UsuarioAutenticado
from modules.clases import service as clases_service
from modules.clases.dependencies import verificar_acceso_a_clase, verificar_profesor_dueno_de_clase
from modules.clasificacion import service
from modules.clasificacion.schemas import (
    ClasificacionGeneralOut,
    ClasificacionJornadaOut,
    ValidacionSeleccionOut,
)
from modules.jornadas import service as jornadas_service

router = APIRouter(prefix="/clasificacion", tags=["clasificacion"])


@router.get("/jornada/{jornada_id}", response_model=list[ClasificacionJornadaOut])
async def api_clasificacion_de_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                        usuario: UsuarioAutenticado = Depends(obtener_usuario_actual)):
    jornada = await jornadas_service.obtener_jornada(pool, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    if usuario.tipo == "profesor":
        if await clases_service.obtener_clase_del_profesor(pool, jornada["clase_id"], usuario.id) is None:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
    elif usuario.clase_id != jornada["clase_id"]:
        raise HTTPException(status_code=403, detail="No perteneces a esta clase.")
    return await service.clasificacion_de_jornada(pool, jornada_id)


@router.get("/general", response_model=list[ClasificacionGeneralOut])
async def api_clasificacion_general(clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                     _=Depends(verificar_acceso_a_clase)):
    return await service.clasificacion_general(pool, clase_id)


@router.get("/podio", response_model=list[ClasificacionGeneralOut])
async def api_podio(clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                     _=Depends(verificar_acceso_a_clase)):
    return await service.podio(pool, clase_id)


@router.get("/validacion-seleccion", response_model=list[ValidacionSeleccionOut])
async def api_validar_seleccion(clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                 _=Depends(verificar_profesor_dueno_de_clase)):
    return await service.validar_seleccion_completa(pool, clase_id)


@router.get("/vista/general", response_class=HTMLResponse)
async def vista_clasificacion_general(request: Request, clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                       _=Depends(verificar_acceso_a_clase)):
    clasificacion = await service.clasificacion_general(pool, clase_id)
    return templates.TemplateResponse(
        request, "clasificacion/general.html", {"clasificacion": clasificacion, "clase_id": clase_id}
    )


@router.get("/vista/validacion-seleccion", response_class=HTMLResponse)
async def vista_validacion_seleccion(request: Request, clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                      _=Depends(verificar_profesor_dueno_de_clase)):
    validacion = await service.validar_seleccion_completa(pool, clase_id)
    return templates.TemplateResponse(
        request, "clasificacion/validacion_seleccion.html", {"validacion": validacion, "clase_id": clase_id}
    )
