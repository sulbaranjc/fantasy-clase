"""Punto de entrada de la aplicación FastAPI.

Registra el logging, el ciclo de vida del pool de MySQL, los archivos
estáticos, y los routers de cada módulo (uno por entidad de negocio).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.database import close_pool, get_pool, init_pool
from core.logging_config import configurar_logging
from core.templates import templates
from modules.alumnos.router import router as alumnos_router
from modules.auth.dependencies import obtener_usuario_actual_opcional
from modules.auth.middleware import UsuarioActualMiddleware
from modules.auth.router import router as auth_router
from modules.auth.schemas import UsuarioAutenticado
from modules.catalogo_puntos.router import router as catalogo_puntos_router
from modules.clasificacion.router import router as clasificacion_router
from modules.clases import service as clases_service
from modules.clases.router import router as clases_router
from modules.eventos.router import router as eventos_router
from modules.jornadas import service as jornadas_service
from modules.jornadas.router import router as jornadas_router
from modules.plantillas.router import router as plantillas_router

configurar_logging()
logger = logging.getLogger("fantasy_clase")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicación: creando pool de conexión a MySQL...")
    await init_pool()
    yield
    logger.info("Deteniendo aplicación: cerrando pool de conexión...")
    await close_pool()


app = FastAPI(title="Fantasy de Clase", lifespan=lifespan)

app.add_middleware(UsuarioActualMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers de módulos de negocio. Cada módulo nuevo (clases, eventos,
# jornadas, plantillas, clasificacion, auth...) se registra aquí conforme
# se vaya implementando en iteraciones sucesivas.
app.include_router(alumnos_router)
app.include_router(auth_router)
app.include_router(catalogo_puntos_router)
app.include_router(clasificacion_router)
app.include_router(clases_router)
app.include_router(eventos_router)
app.include_router(jornadas_router)
app.include_router(plantillas_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, pool=Depends(get_pool),
                usuario: UsuarioAutenticado | None = Depends(obtener_usuario_actual_opcional)):
    """Portada: sin sesión es una invitación a entrar; con sesión es el
    panel de navegación (dashboard) hacia el resto de módulos, distinto
    para profesor (elige entre sus clases) y alumno (va directo a la suya)."""
    contexto = {"usuario": usuario}

    if usuario is not None and usuario.tipo == "profesor":
        contexto["clases"] = await clases_service.listar_clases_de_profesor(pool, usuario.id)
    elif usuario is not None and usuario.tipo == "alumno":
        contexto["jornada_activa"] = await jornadas_service.obtener_jornada_activa(pool, usuario.clase_id)

    return templates.TemplateResponse(request, "index.html", contexto)


@app.get("/salud")
async def salud():
    """Health check: confirma que la app responde y que el pool de MySQL
    está inicializado (no ejecuta ninguna query, solo verifica el objeto)."""
    pool_ok = False
    try:
        get_pool()
        pool_ok = True
    except RuntimeError:
        pool_ok = False
    return {"estado": "ok", "base_de_datos": "conectada" if pool_ok else "no disponible"}
