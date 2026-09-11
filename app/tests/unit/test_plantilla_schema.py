"""Pruebas unitarias de las reglas de FORMA de PlantillaCreate (sin BD).

`manager_id` no forma parte del schema (viaja aparte, resuelto de la
sesión); la regla "el manager debe incluirse a sí mismo" se prueba en
`test_plantilla_reglas.py`, contra `fichar_plantilla`.
"""
import pytest
from pydantic import ValidationError

from modules.plantillas.schemas import PlantillaCreate

BASE = {"jornada_id": 1, "jugadores_ids": [1, 2, 3, 4, 5], "capitan_id": 1}


def test_acepta_una_combinacion_valida():
    plantilla = PlantillaCreate(**BASE)
    assert plantilla.jugadores_ids == [1, 2, 3, 4, 5]


def test_rechaza_jugador_repetido():
    with pytest.raises(ValidationError):
        PlantillaCreate(**{**BASE, "jugadores_ids": [1, 2, 3, 4, 1]})


def test_rechaza_menos_de_cinco_jugadores():
    with pytest.raises(ValidationError):
        PlantillaCreate(**{**BASE, "jugadores_ids": [1, 2, 3, 4]})


def test_rechaza_mas_de_cinco_jugadores():
    with pytest.raises(ValidationError):
        PlantillaCreate(**{**BASE, "jugadores_ids": [1, 2, 3, 4, 5, 6]})


def test_rechaza_capitan_que_no_esta_entre_los_cinco():
    with pytest.raises(ValidationError):
        PlantillaCreate(**{**BASE, "capitan_id": 99})
