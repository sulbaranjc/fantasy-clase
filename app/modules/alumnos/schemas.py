"""Modelos Pydantic del módulo alumnos: única fuente de verdad de validación
de entrada (la validación en JavaScript en el navegador es solo una ayuda
de UX, nunca sustituye a esta capa)."""
from pydantic import BaseModel, Field


class AlumnoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=3, max_length=60, pattern=r"^[a-z0-9._-]+$")
    password: str = Field(min_length=4, max_length=100)


class AlumnoOut(BaseModel):
    id: int
    nombre: str
    username: str
    valor_actual: int
