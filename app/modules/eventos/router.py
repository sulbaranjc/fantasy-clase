"""Endpoints del módulo eventos: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.alumnos import service as alumnos_service
from modules.catalogo_puntos import service as catalogo_service
from modules.eventos import service
from modules.eventos.schemas import EventoCreate, EventoOut, EventoUpdate
from modules.eventos.service import (
    AlumnoInvalidoError,
    EventoInexistenteError,
    JornadaInvalidaError,
    TipoEventoInvalidoError,
)
router = APIRouter(prefix="/eventos", tags=["eventos"])

_ERRORES_DE_CONSISTENCIA = (AlumnoInvalidoError, JornadaInvalidaError, TipoEventoInvalidoError)


@router.post("", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
async def api_crear_evento(clase_id: int, datos: EventoCreate, pool: asyncmy.Pool = Depends(get_pool)):
    try:
        evento_id = await service.crear_evento(pool, clase_id, datos)
    except _ERRORES_DE_CONSISTENCIA as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return await service.obtener_evento(pool, evento_id)


@router.get("/alumno/{alumno_id}", response_model=list[EventoOut])
async def api_listar_eventos_de_alumno(alumno_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_eventos_de_alumno(pool, alumno_id)


@router.get("/jornada/{jornada_id}", response_model=list[EventoOut])
async def api_listar_eventos_de_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    return await service.listar_eventos_de_jornada(pool, jornada_id)


# Rutas específicas (arriba) antes de la genérica "/{evento_id}" (abajo):
# aunque FastAPI ya resuelve esto correctamente por el tipo `int` del
# parámetro, declararlas en este orden evita depender de ese detalle.
@router.get("/{evento_id}", response_model=EventoOut)
async def api_obtener_evento(evento_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    evento = await service.obtener_evento(pool, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


@router.put("/{evento_id}", response_model=EventoOut)
async def api_actualizar_evento(evento_id: int, datos: EventoUpdate, pool: asyncmy.Pool = Depends(get_pool)):
    try:
        await service.actualizar_evento(pool, evento_id, datos)
    except EventoInexistenteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TipoEventoInvalidoError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return await service.obtener_evento(pool, evento_id)


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_eliminar_evento(evento_id: int, pool: asyncmy.Pool = Depends(get_pool)):
    if await service.obtener_evento(pool, evento_id) is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    await service.eliminar_evento(pool, evento_id)


@router.get("/vista/por-jornada", response_class=HTMLResponse)
async def vista_eventos_de_jornada(request: Request, jornada_id: int, clase_id: int,
                                    pool: asyncmy.Pool = Depends(get_pool)):
    eventos = await service.listar_eventos_de_jornada(pool, jornada_id)
    catalogo = await catalogo_service.listar_eventos(pool, clase_id, solo_activos=True)
    alumnos = await alumnos_service.listar_alumnos(pool, clase_id)

    nombre_alumno = {a["id"]: a["nombre"] for a in alumnos}
    nombre_evento = {c["id"]: c["nombre"] for c in catalogo}
    for evento in eventos:
        evento["nombre_alumno"] = nombre_alumno.get(evento["alumno_id"], "—")
        evento["nombre_tipo"] = nombre_evento.get(evento["catalogo_punto_id"], "—")

    return templates.TemplateResponse(
        request, "eventos/listado.html",
        {"eventos": eventos, "catalogo": catalogo, "alumnos": alumnos,
         "jornada_id": jornada_id, "clase_id": clase_id},
    )
