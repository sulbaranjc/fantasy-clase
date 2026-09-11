"""Punto de entrada de la aplicación FastAPI.

Registra el logging, el ciclo de vida del pool de MySQL, los archivos
estáticos, y los routers de cada módulo (uno por entidad de negocio).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.database import close_pool, get_pool, init_pool
from core.logging_config import configurar_logging
from core.templates import templates
from modules.alumnos.router import router as alumnos_router
from modules.catalogo_puntos.router import router as catalogo_puntos_router
from modules.clases.router import router as clases_router
from modules.jornadas.router import router as jornadas_router

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

app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers de módulos de negocio. Cada módulo nuevo (clases, eventos,
# jornadas, plantillas, clasificacion, auth...) se registra aquí conforme
# se vaya implementando en iteraciones sucesivas.
app.include_router(alumnos_router)
app.include_router(catalogo_puntos_router)
app.include_router(clases_router)
app.include_router(jornadas_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


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
