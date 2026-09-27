"""Endpoints del módulo clases: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí.

Todos requieren una sesión de profesor: `profesor_id` ya no se recibe como
parámetro explícito, se toma de la sesión JWT (`requiere_profesor`).
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.templates import templates
from modules.auth.dependencies import requiere_profesor
from modules.auth.schemas import UsuarioAutenticado
from modules.clases import service
from modules.clases.dependencies import verificar_profesor_dueno_de_clase
from modules.clases.schemas import ClaseCreate, ClaseOut, ClaseUpdate

router = APIRouter(prefix="/clases", tags=["clases"])


@router.post("", response_model=ClaseOut, status_code=status.HTTP_201_CREATED)
async def api_crear_clase(datos: ClaseCreate, pool: asyncmy.Pool = Depends(get_pool),
                           profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    clase_id = await service.crear_clase(pool, profesor.id, datos)
    return await service.obtener_clase(pool, clase_id)


@router.get("", response_model=list[ClaseOut])
async def api_listar_clases(pool: asyncmy.Pool = Depends(get_pool),
                             profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    return await service.listar_clases_de_profesor(pool, profesor.id)


@router.get("/{clase_id}", response_model=ClaseOut)
async def api_obtener_clase(clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                             profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    clase = await service.obtener_clase_del_profesor(pool, clase_id, profesor.id)
    if clase is None:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    return clase


@router.put("/{clase_id}", response_model=ClaseOut)
async def api_actualizar_clase(clase_id: int, datos: ClaseUpdate, pool: asyncmy.Pool = Depends(get_pool),
                                profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    if await service.obtener_clase_del_profesor(pool, clase_id, profesor.id) is None:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    await service.actualizar_clase(pool, clase_id, datos)
    return await service.obtener_clase(pool, clase_id)


@router.get("/vista/listado", response_class=HTMLResponse)
async def vista_listado_clases(request: Request, pool: asyncmy.Pool = Depends(get_pool),
                                profesor: UsuarioAutenticado = Depends(requiere_profesor)):
    clases = await service.listar_clases_de_profesor(pool, profesor.id)
    return templates.TemplateResponse(request, "clases/listado.html", {"clases": clases})


@router.get("/{clase_id}/vista/dashboard", response_class=HTMLResponse)
async def vista_dashboard_clase(request: Request, clase_id: int, pool: asyncmy.Pool = Depends(get_pool),
                                 _=Depends(verificar_profesor_dueno_de_clase)):
    """Panel de navegación de una clase concreta: desde aquí el profesor
    entra a cada módulo (alumnos, catálogo, calendario, clasificación...)
    ya con la clase resuelta."""
    clase = await service.obtener_clase(pool, clase_id)
    return templates.TemplateResponse(request, "clases/dashboard.html", {"clase": clase})
