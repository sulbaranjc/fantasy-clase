"""Endpoints del módulo jornadas: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.auth.dependencies import obtener_usuario_actual, requiere_profesor
from modules.auth.schemas import UsuarioAutenticado
from modules.clases import service as clases_service
from modules.clases.dependencies import verificar_acceso_a_clase, verificar_profesor_dueno_de_clase
from modules.jornadas import service
from modules.jornadas.schemas import JornadaOut
from modules.jornadas.service import CalendarioYaGeneradoError, ClaseInexistenteError

router = APIRouter(prefix="/jornadas", tags=["jornadas"])


async def _verificar_acceso_a_jornada(pool: asyncmy.Pool, jornada_id: int,
                                       usuario: UsuarioAutenticado) -> dict:
    """Encuentra la jornada, o 404 si no existe o su clase no es
    accesible para este usuario (profesor dueño, o alumno de esa clase)."""
    jornada = await service.obtener_jornada(pool, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    if usuario.tipo == "profesor":
        if await clases_service.obtener_clase_del_profesor(pool, jornada["clase_id"], usuario.id) is None:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
    elif usuario.clase_id != jornada["clase_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No perteneces a esta clase.")
    return jornada


async def _verificar_jornada_del_profesor(pool: asyncmy.Pool, jornada_id: int, profesor_id: int) -> dict:
    """Como `_verificar_acceso_a_jornada`, pero solo para el profesor
    dueño: usada por las acciones administrativas (abrir/cerrar fichajes
    a mano), que un alumno nunca debe poder disparar."""
    jornada = await service.obtener_jornada(pool, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    if await clases_service.obtener_clase_del_profesor(pool, jornada["clase_id"], profesor_id) is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    return jornada


@router.post("/generar", response_model=list[JornadaOut], status_code=status.HTTP_201_CREATED)
async def api_generar_calendario(clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                  _=Depends(verificar_profesor_dueno_de_clase)):
    try:
        return await service.generar_y_guardar_calendario(pool, clase_id)
    except ClaseInexistenteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CalendarioYaGeneradoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[JornadaOut])
async def api_listar_jornadas(clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                               _=Depends(verificar_acceso_a_clase)):
    return await service.listar_jornadas(pool, clase_id)


@router.get("/{jornada_id}", response_model=JornadaOut)
async def api_obtener_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool),
                               usuario: UsuarioAutenticado = Depends(obtener_usuario_actual)):
    return await _verificar_acceso_a_jornada(pool, jornada_id, usuario)


@router.post("/{jornada_id}/abrir-fichajes", response_model=JornadaOut)
async def api_abrir_fichajes(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool),
                              profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    await _verificar_jornada_del_profesor(pool, jornada_id, profesor.id)
    return await service.abrir_fichajes_ahora(pool, jornada_id)


@router.post("/{jornada_id}/cerrar-fichajes", response_model=JornadaOut)
async def api_cerrar_fichajes(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool),
                               profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    await _verificar_jornada_del_profesor(pool, jornada_id, profesor.id)
    return await service.cerrar_fichajes_ahora(pool, jornada_id)


@router.get("/vista/listado", response_class=HTMLResponse)
async def vista_listado_jornadas(request: Request, clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                  usuario: UsuarioAutenticado = Depends(verificar_acceso_a_clase)):
    jornadas = await service.listar_jornadas(pool, clase_id)
    jornada_activa_id = None
    if usuario.tipo == "alumno":
        jornada_activa = await service.obtener_jornada_activa(pool, clase_id)
        jornada_activa_id = jornada_activa["id"] if jornada_activa else None

    # El campo `cerrada` de la jornada nunca se actualiza automáticamente
    # (no hay todavía un cierre de jornada automatizado); el estado real
    # que le importa a quien mira el calendario es si su ventana de
    # fichajes ya pasó, está abierta ahora, o todavía no ha llegado.
    ahora = datetime.now()
    for jornada in jornadas:
        if ahora < jornada["apertura_fichajes"]:
            jornada["estado_ventana"] = "proxima"
        elif ahora <= jornada["cierre_fichajes"]:
            jornada["estado_ventana"] = "abierta"
        else:
            jornada["estado_ventana"] = "cerrada"

    return templates.TemplateResponse(
        request, "jornadas/listado.html",
        {
            "jornadas": jornadas, "clase_id": clase_id, "es_profesor": usuario.tipo == "profesor",
            "jornada_activa_id": jornada_activa_id,
        },
    )
