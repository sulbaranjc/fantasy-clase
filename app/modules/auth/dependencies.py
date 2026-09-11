"""Dependencias de FastAPI para proteger rutas con la sesión JWT en cookie.

Pensadas para que los demás módulos las importen cuando llegue el momento
de dejar de recibir profesor_id/clase_id/manager_id como parámetro
explícito y tomarlos de la sesión autenticada.
"""
import jwt
from fastapi import Depends, HTTPException, Request, status

from core.security import COOKIE_NAME, decodificar_token
from modules.auth.schemas import UsuarioAutenticado
from modules.auth.service import usuario_desde_claims


async def obtener_usuario_actual_opcional(request: Request) -> UsuarioAutenticado | None:
    """Como `obtener_usuario_actual`, pero devuelve None en vez de lanzar
    401 cuando no hay sesión — para vistas que se comportan distinto según
    haya o no alguien identificado, sin exigirlo."""
    token = request.cookies.get(COOKIE_NAME)
    if token is None:
        return None
    try:
        claims = decodificar_token(token)
    except jwt.PyJWTError:
        return None
    return UsuarioAutenticado(**usuario_desde_claims(claims))


async def obtener_usuario_actual(
    usuario: UsuarioAutenticado | None = Depends(obtener_usuario_actual_opcional),
) -> UsuarioAutenticado:
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No has iniciado sesión.")
    return usuario


async def requiere_profesor(
    usuario: UsuarioAutenticado = Depends(obtener_usuario_actual),
) -> UsuarioAutenticado:
    if usuario.tipo != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere una sesión de profesor.")
    return usuario


async def requiere_alumno(
    usuario: UsuarioAutenticado = Depends(obtener_usuario_actual),
) -> UsuarioAutenticado:
    if usuario.tipo != "alumno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere una sesión de alumno.")
    return usuario
