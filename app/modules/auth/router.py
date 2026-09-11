"""Endpoints del módulo auth: reciben la petición HTTP y delegan en
`service`. Sin lógica de negocio aquí."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
import asyncmy

from core.database import get_pool
from core.security import COOKIE_NAME
from core.templates import templates
from modules.auth import service
from modules.auth.dependencies import obtener_usuario_actual
from modules.auth.schemas import LoginRequest, UsuarioAutenticado
from modules.auth.service import CredencialesInvalidasError

router = APIRouter(prefix="/auth", tags=["auth"])

# Misma duración que el propio JWT (Settings.jwt_expira_minutos): no tiene
# sentido que la cookie sobreviva más que el token que contiene.
_MAX_AGE_COOKIE_SEGUNDOS = 60 * 60 * 24 * 14


def _guardar_cookie_de_sesion(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME, value=token, httponly=True, samesite="lax", max_age=_MAX_AGE_COOKIE_SEGUNDOS,
    )


@router.post("/profesor/login", response_model=UsuarioAutenticado)
async def login_profesor(datos: LoginRequest, response: Response, pool: asyncmy.Pool = Depends(get_pool)):
    try:
        token, usuario = await service.login_profesor(pool, datos.username, datos.password)
    except CredencialesInvalidasError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    _guardar_cookie_de_sesion(response, token)
    return usuario


@router.post("/alumno/login", response_model=UsuarioAutenticado)
async def login_alumno(datos: LoginRequest, response: Response, pool: asyncmy.Pool = Depends(get_pool)):
    try:
        token, usuario = await service.login_alumno(pool, datos.username, datos.password)
    except CredencialesInvalidasError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    _guardar_cookie_de_sesion(response, token)
    return usuario


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"mensaje": "Sesión cerrada."}


@router.get("/me", response_model=UsuarioAutenticado)
async def quien_soy(usuario: UsuarioAutenticado = Depends(obtener_usuario_actual)):
    return usuario


@router.get("/vista/login", response_class=HTMLResponse)
async def vista_login(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", {})
