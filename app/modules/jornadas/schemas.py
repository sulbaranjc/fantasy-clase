"""Modelos Pydantic del módulo jornadas.

No hay un "Create" con datos de entrada de usuario: las jornadas se generan
automáticamente a partir de las fechas y parámetros de la clase, no las
teclea nadie a mano.
"""
from datetime import date, datetime

from pydantic import BaseModel


class JornadaOut(BaseModel):
    id: int
    clase_id: int
    numero: int
    fecha_inicio: date
    fecha_fin: date
    apertura_fichajes: datetime
    cierre_fichajes: datetime
    cerrada: bool
