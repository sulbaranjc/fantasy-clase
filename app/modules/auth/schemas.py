"""Modelos Pydantic del módulo auth (única fuente de verdad de validación
de entrada)."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=1, max_length=100)


class UsuarioAutenticado(BaseModel):
    tipo: str  # "profesor" | "alumno"
    id: int
    nombre: str
    clase_id: int | None = None  # solo aplica a alumnos
