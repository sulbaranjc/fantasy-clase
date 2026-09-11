"""Modelos Pydantic del módulo eventos (única fuente de verdad de
validación de entrada)."""
from datetime import date

from pydantic import BaseModel, Field


class EventoCreate(BaseModel):
    alumno_id: int
    jornada_id: int
    catalogo_punto_id: int
    fecha: date
    nota_numerica: float | None = Field(default=None, ge=0, le=10)
    comentario: str | None = Field(default=None, max_length=255)


class EventoUpdate(BaseModel):
    """No se permite cambiar de alumno o de jornada un evento ya creado
    (si se registró sobre la persona o la jornada equivocada, se borra y
    se crea de nuevo); sí se puede corregir la categoría, la fecha, la
    nota o el comentario — incluida una jornada ya cerrada, cuya
    corrección debe repercutir en el recálculo del valor de mercado."""
    catalogo_punto_id: int
    fecha: date
    nota_numerica: float | None = Field(default=None, ge=0, le=10)
    comentario: str | None = Field(default=None, max_length=255)


class EventoOut(BaseModel):
    id: int
    clase_id: int
    alumno_id: int
    jornada_id: int
    catalogo_punto_id: int
    fecha: date
    nota_numerica: float | None
    comentario: str | None
    puntos_otorgados: int
