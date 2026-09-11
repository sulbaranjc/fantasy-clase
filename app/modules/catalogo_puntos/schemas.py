"""Modelos Pydantic del módulo catalogo_puntos (única fuente de verdad de
validación de entrada)."""
from pydantic import BaseModel, Field


class CatalogoPuntoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    puntos: int = Field(ge=-100, le=100, description="Puede ser negativo")


class CatalogoPuntoUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    puntos: int = Field(ge=-100, le=100)
    activo: bool = True


class CatalogoPuntoOut(BaseModel):
    id: int
    clase_id: int
    nombre: str
    puntos: int
    activo: bool
