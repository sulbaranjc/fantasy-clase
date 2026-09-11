"""Modelos Pydantic del módulo plantillas (única fuente de verdad de
validación de entrada).

`manager_id` no forma parte de la entrada: quien ficha es siempre el
alumno autenticado (nunca se acepta que un alumno finche "en nombre" de
otro), así que el router lo toma de la sesión, no del payload. Por eso la
regla "el manager debe incluirse a sí mismo entre los 5" se valida en
`service.py` (ahí es donde se conoce el manager real), no aquí.
"""
from pydantic import BaseModel, Field, model_validator


class PlantillaCreate(BaseModel):
    jornada_id: int
    jugadores_ids: list[int] = Field(min_length=5, max_length=5)
    capitan_id: int

    @model_validator(mode="after")
    def validar_forma(self) -> "PlantillaCreate":
        if len(set(self.jugadores_ids)) != 5:
            raise ValueError("Los 5 jugadores deben ser distintos: no se permite fichar dos veces al mismo.")
        if self.capitan_id not in self.jugadores_ids:
            raise ValueError("El capitán debe ser uno de los 5 jugadores fichados.")
        return self


class JugadorFichadoOut(BaseModel):
    jugador_id: int
    valor_al_fichar: int


class PlantillaOut(BaseModel):
    id: int
    jornada_id: int
    manager_id: int
    capitan_id: int
    generada_automaticamente: bool
    jugadores: list[JugadorFichadoOut]
