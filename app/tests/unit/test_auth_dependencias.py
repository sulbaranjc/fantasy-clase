"""Pruebas unitarias de `requiere_profesor` / `requiere_alumno`: se les
pasa un UsuarioAutenticado ya resuelto a mano (sin pasar por HTTP ni por
la cookie), comprobando solo la regla de autorización por tipo."""
import pytest
from fastapi import HTTPException

from modules.auth.dependencies import requiere_alumno, requiere_profesor
from modules.auth.schemas import UsuarioAutenticado

PROFESOR = UsuarioAutenticado(tipo="profesor", id=1, nombre="Álvaro")
ALUMNO = UsuarioAutenticado(tipo="alumno", id=2, nombre="María", clase_id=5)


@pytest.mark.asyncio
async def test_requiere_profesor_acepta_a_un_profesor():
    assert await requiere_profesor(usuario=PROFESOR) == PROFESOR


@pytest.mark.asyncio
async def test_requiere_profesor_rechaza_a_un_alumno():
    with pytest.raises(HTTPException) as exc_info:
        await requiere_profesor(usuario=ALUMNO)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_requiere_alumno_acepta_a_un_alumno():
    assert await requiere_alumno(usuario=ALUMNO) == ALUMNO


@pytest.mark.asyncio
async def test_requiere_alumno_rechaza_a_un_profesor():
    with pytest.raises(HTTPException) as exc_info:
        await requiere_alumno(usuario=PROFESOR)
    assert exc_info.value.status_code == 403
