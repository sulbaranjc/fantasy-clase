"""Middleware que deja el usuario autenticado (o None) en `request.state`.

FastAPI/Jinja2Templates inyecta `request` automáticamente en el contexto
de cualquier plantilla renderizada con `TemplateResponse(request, ...)`,
así que `base.html` puede leer `request.state.usuario` en la navbar sin
que cada vista tenga que pasarlo explícitamente en su contexto.
"""
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.security import COOKIE_NAME, decodificar_token
from modules.auth.schemas import UsuarioAutenticado
from modules.auth.service import usuario_desde_claims


class UsuarioActualMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.usuario = None
        token = request.cookies.get(COOKIE_NAME)
        if token:
            try:
                claims = decodificar_token(token)
                request.state.usuario = UsuarioAutenticado(**usuario_desde_claims(claims))
            except jwt.PyJWTError:
                pass
        return await call_next(request)
