"""Dependencias de FastAPI para verificar el acceso a una clase concreta.

Reutilizadas por todos los módulos que cuelgan de una clase (alumnos,
catalogo_puntos, jornadas, eventos, plantillas, clasificacion): declarar
`clase_id: int` como parámetro de estas dependencias hace que FastAPI lo
resuelva del propio query/path del endpoint, igual que si fuera un
parámetro normal de la función.
"""
from fastapi import Depends, HTTPException, status
import asyncmy

from core.database import get_pool
from modules.auth.dependencies import obtener_usuario_actual, requiere_profesor
from modules.auth.schemas import UsuarioAutenticado
from modules.clases import service


async def verificar_profesor_dueno_de_clase(
    clase_id: int,
    pool: asyncmy.Pool = Depends(get_pool),
    profesor: UsuarioAutenticado = Depends(requiere_profesor),
) -> UsuarioAutenticado:
    """Para operaciones reservadas al profesor (crear/editar/borrar):
    exige sesión de profesor Y que la clase le pertenezca."""
    clase = await service.obtener_clase_del_profesor(pool, clase_id, profesor.id)
    if clase is None:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    return profesor


async def verificar_acceso_a_clase(
    clase_id: int,
    pool: asyncmy.Pool = Depends(get_pool),
    usuario: UsuarioAutenticado = Depends(obtener_usuario_actual),
) -> UsuarioAutenticado:
    """Para operaciones de lectura compartidas: permite al profesor dueño
    de la clase, o a un alumno que pertenezca a ella."""
    if usuario.tipo == "profesor":
        clase = await service.obtener_clase_del_profesor(pool, clase_id, usuario.id)
        if clase is None:
            raise HTTPException(status_code=404, detail="Clase no encontrada")
    else:
        if usuario.clase_id != clase_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No perteneces a esta clase.")
    return usuario
