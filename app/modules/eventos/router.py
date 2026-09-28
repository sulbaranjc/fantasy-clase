"""Endpoints del módulo eventos: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí.

Registrar/editar/borrar eventos queda reservado al profesor (regla de
negocio explícita: solo él puntúa a los alumnos). Consultar el propio
historial se permite también al alumno afectado."""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.alumnos import repository as alumnos_repository
from modules.alumnos import service as alumnos_service
from modules.auth.dependencies import obtener_usuario_actual, requiere_profesor
from modules.auth.schemas import UsuarioAutenticado
from modules.catalogo_puntos import service as catalogo_service
from modules.clases import service as clases_service
from modules.clases.dependencies import verificar_profesor_dueno_de_clase
from modules.eventos import service
from modules.eventos.schemas import EventoCreate, EventoOut, EventoUpdate
from modules.eventos.service import (
    AlumnoInvalidoError,
    EventoInexistenteError,
    ImportacionInvalidaError,
    JornadaInvalidaError,
    TipoEventoInvalidoError,
)
from modules.jornadas import service as jornadas_service

router = APIRouter(prefix="/eventos", tags=["eventos"])

_ERRORES_DE_CONSISTENCIA = (AlumnoInvalidoError, JornadaInvalidaError, TipoEventoInvalidoError)


async def _verificar_evento_del_profesor(pool: asyncmy.Pool, evento_id: int, profesor_id: int) -> dict:
    evento = await service.obtener_evento(pool, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    if await clases_service.obtener_clase_del_profesor(pool, evento["clase_id"], profesor_id) is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


@router.post("", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
async def api_crear_evento(clase_id: int, datos: EventoCreate, pool: asyncmy.Pool = Depends(get_pool),
                            _=Depends(verificar_profesor_dueno_de_clase)):
    try:
        evento_id = await service.crear_evento(pool, clase_id, datos)
    except _ERRORES_DE_CONSISTENCIA as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return await service.obtener_evento(pool, evento_id)


@router.post("/importar", response_model=list[EventoOut], status_code=status.HTTP_201_CREATED)
async def api_importar_eventos(clase_id: int, archivo: UploadFile, pool: asyncmy.Pool = Depends(get_pool),
                                _=Depends(verificar_profesor_dueno_de_clase)):
    contenido = (await archivo.read()).decode("utf-8")
    try:
        ids_creados = await service.importar_eventos_desde_archivo(pool, clase_id, contenido)
    except ImportacionInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [await service.obtener_evento(pool, evento_id) for evento_id in ids_creados]


@router.get("/alumno/{alumno_id}", response_model=list[EventoOut])
async def api_listar_eventos_de_alumno(alumno_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                        usuario: UsuarioAutenticado = Depends(obtener_usuario_actual)):
    alumno = await alumnos_repository.obtener_por_id(pool, alumno_id)
    if alumno is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    if usuario.tipo == "alumno":
        if usuario.id != alumno_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes ver tu propio historial.")
    elif await clases_service.obtener_clase_del_profesor(pool, alumno["clase_id"], usuario.id) is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    return await service.listar_eventos_de_alumno(pool, alumno_id)


@router.get("/jornada/{jornada_id}", response_model=list[EventoOut])
async def api_listar_eventos_de_jornada(jornada_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                         profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    jornada = await jornadas_service.obtener_jornada(pool, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    if await clases_service.obtener_clase_del_profesor(pool, jornada["clase_id"], profesor.id) is None:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    return await service.listar_eventos_de_jornada(pool, jornada_id)


@router.get("/{evento_id}", response_model=EventoOut)
async def api_obtener_evento(evento_id: int, pool: asyncmy.Pool = Depends(get_pool),
                              profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    return await _verificar_evento_del_profesor(pool, evento_id, profesor.id)


@router.put("/{evento_id}", response_model=EventoOut)
async def api_actualizar_evento(evento_id: int, datos: EventoUpdate, pool: asyncmy.Pool = Depends(get_pool),
                                 profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    await _verificar_evento_del_profesor(pool, evento_id, profesor.id)
    try:
        await service.actualizar_evento(pool, evento_id, datos)
    except EventoInexistenteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TipoEventoInvalidoError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return await service.obtener_evento(pool, evento_id)


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_eliminar_evento(evento_id: int, pool: asyncmy.Pool = Depends(get_pool),
                               profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    await _verificar_evento_del_profesor(pool, evento_id, profesor.id)
    await service.eliminar_evento(pool, evento_id)


@router.get("/vista/por-jornada", response_class=HTMLResponse)
async def vista_eventos_de_jornada(request: Request, jornada_id: int, clase_id: int,
                                    pool: asyncmy.Pool = Depends(get_pool),
                                    _=Depends(verificar_profesor_dueno_de_clase)):
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
