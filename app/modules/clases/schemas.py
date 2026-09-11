"""Modelos Pydantic del módulo clases (única fuente de verdad de validación
de entrada)."""
from datetime import date

from pydantic import BaseModel, Field, model_validator


class ClaseCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    fecha_inicio: date
    fecha_fin: date
    duracion_jornada_dias: int = Field(default=14, ge=1, le=60)
    ventana_fichaje_horas: int = Field(default=24, ge=1, le=168)
    valor_inicial_jugador: int = Field(default=20, ge=1)
    valor_minimo_jugador: int = Field(default=10, ge=0)
    factor_recalculo_valor: float = Field(default=0.10, ge=0, le=1)
    presupuesto_manager: int = Field(default=120, ge=1)

    @model_validator(mode="after")
    def validar_fechas_y_valores(self) -> "ClaseCreate":
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio.")
        if self.valor_minimo_jugador > self.valor_inicial_jugador:
            raise ValueError("El valor mínimo no puede ser mayor que el valor inicial del jugador.")
        return self


class ClaseOut(BaseModel):
    id: int
    profesor_id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    duracion_jornada_dias: int
    ventana_fichaje_horas: int
    valor_inicial_jugador: int
    valor_minimo_jugador: int
    factor_recalculo_valor: float
    presupuesto_manager: int
    activa: bool
