"""Endpoints del módulo catalogo_puntos: reciben la petición HTTP y
delegan en `service`. Sin lógica de negocio aquí.

Es una herramienta de configuración de la clase: todo el módulo queda
reservado al profesor dueño (los alumnos no necesitan gestionarlo)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.auth.dependencies import requiere_profesor
from modules.auth.schemas import UsuarioAutenticado
from modules.catalogo_puntos import service
from modules.catalogo_puntos.schemas import CatalogoPuntoCreate, CatalogoPuntoOut, CatalogoPuntoUpdate
from modules.catalogo_puntos.service import NombreDuplicadoError
from modules.clases import service as clases_service
from modules.clases.dependencies import verificar_profesor_dueno_de_clase

router = APIRouter(prefix="/catalogo-puntos", tags=["catalogo_puntos"])


async def _verificar_evento_del_profesor(pool: asyncmy.Pool, catalogo_punto_id: int, profesor_id: int) -> dict:
    """Encuentra el evento del catálogo, o 404 si no existe o su clase no
    pertenece a este profesor (mismo tratamiento para ambos casos)."""
    evento = await service.obtener_evento(pool, catalogo_punto_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")
    if await clases_service.obtener_clase_del_profesor(pool, evento["clase_id"], profesor_id) is None:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")
    return evento


@router.post("", response_model=CatalogoPuntoOut, status_code=status.HTTP_201_CREATED)
async def api_crear_evento(clase_id: int, datos: CatalogoPuntoCreate, pool: asyncmy.Pool = Depends(get_pool),
                            _=Depends(verificar_profesor_dueno_de_clase)):
    try:
        evento_id = await service.crear_evento(pool, clase_id, datos)
    except NombreDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return await service.obtener_evento(pool, evento_id)


@router.get("", response_model=list[CatalogoPuntoOut])
async def api_listar_eventos(clase_id: int, solo_activos: bool = False, pool: asyncmy.Pool = Depends(get_pool),
                              _=Depends(verificar_profesor_dueno_de_clase)):
    return await service.listar_eventos(pool, clase_id, solo_activos)


@router.get("/{catalogo_punto_id}", response_model=CatalogoPuntoOut)
async def api_obtener_evento(catalogo_punto_id: int, pool: asyncmy.Pool = Depends(get_pool),
                              profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    return await _verificar_evento_del_profesor(pool, catalogo_punto_id, profesor.id)


@router.put("/{catalogo_punto_id}", response_model=CatalogoPuntoOut)
async def api_actualizar_evento(catalogo_punto_id: int, datos: CatalogoPuntoUpdate,
                                 pool: asyncmy.Pool = Depends(get_pool),
                                 profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    await _verificar_evento_del_profesor(pool, catalogo_punto_id, profesor.id)
    try:
        await service.actualizar_evento(pool, catalogo_punto_id, datos)
    except NombreDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return await service.obtener_evento(pool, catalogo_punto_id)


@router.get("/vista/listado", response_class=HTMLResponse)
async def vista_listado_eventos(request: Request, clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                 _=Depends(verificar_profesor_dueno_de_clase)):
    eventos = await service.listar_eventos(pool, clase_id)
    return templates.TemplateResponse(
        request, "catalogo_puntos/listado.html", {"eventos": eventos, "clase_id": clase_id}
    )
