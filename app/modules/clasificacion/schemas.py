"""Modelos Pydantic del módulo clasificacion.

No hay entrada de usuario aquí: todo se calcula a partir de eventos,
plantillas y alumnos ya existentes. No hay tabla `clasificacion` en el
esquema —igual que en el Excel original, es una vista derivada, no datos
almacenados— así que estos modelos son de solo lectura.
"""
from pydantic import BaseModel


class ClasificacionJornadaOut(BaseModel):
    manager_id: int
    jornada_id: int
    capitan_id: int
    puntos_jugadores: dict[int, int]
    total: int
    tiene_plantilla: bool


class ClasificacionGeneralOut(BaseModel):
    manager_id: int
    nombre: str
    puntos_totales: int
    posicion: int


class ValidacionSeleccionOut(BaseModel):
    alumno_id: int
    nombre: str
    veces_fichado: int
    estado: str
