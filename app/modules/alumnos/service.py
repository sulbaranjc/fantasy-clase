"""Lógica de negocio del módulo alumnos.

Las funciones puras (sin FastAPI ni SQL) van primero: son las que se cubren
con pruebas unitarias rápidas. Las funciones que sí tocan base de datos
delegan siempre en `repository`, nunca escriben SQL aquí.
"""
import math

import asyncmy

from core.security import hash_password
from modules.alumnos import repository


def recalcular_valor(valor_anterior: int, puntos_jornada: int, factor: float,
                      valor_minimo: int) -> int:
    """Nuevo valor de mercado de un jugador al cierre de una jornada.

    Regla de negocio (confirmada con Álvaro):
        valor_nuevo = valor_anterior + FLOOR(puntos_jornada * factor)
        nunca por debajo de valor_minimo.

    `factor` es 0.10 por defecto (10% de los puntos obtenidos en la
    jornada), redondeado hacia abajo. Funciona igual con puntos_jornada
    negativos: math.floor(-0.8) == -1, así que una mala jornada también
    puede bajar el valor.
    """
    incremento = math.floor(puntos_jornada * factor)
    return max(valor_anterior + incremento, valor_minimo)


async def listar_alumnos(pool: asyncmy.Pool, clase_id: int) -> list[dict]:
    return await repository.listar_por_clase(pool, clase_id)


async def crear_alumno(pool: asyncmy.Pool, clase_id: int, nombre: str,
                        username: str, password: str, valor_inicial: int) -> int:
    password_hash = hash_password(password)
    return await repository.crear(pool, clase_id, nombre, username, password_hash, valor_inicial)
