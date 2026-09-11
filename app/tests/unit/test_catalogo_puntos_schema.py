"""Pruebas unitarias de las reglas de validación de CatalogoPuntoCreate."""
import pytest
from pydantic import ValidationError

from modules.catalogo_puntos.schemas import CatalogoPuntoCreate


def test_acepta_puntos_negativos():
    evento = CatalogoPuntoCreate(nombre="Trabajo/Examen no entregado", puntos=-10)
    assert evento.puntos == -10


def test_acepta_puntos_positivos():
    evento = CatalogoPuntoCreate(nombre="Examen >9", puntos=6)
    assert evento.puntos == 6


def test_rechaza_nombre_vacio():
    with pytest.raises(ValidationError):
        CatalogoPuntoCreate(nombre="", puntos=1)


def test_rechaza_puntos_fuera_de_rango():
    with pytest.raises(ValidationError):
        CatalogoPuntoCreate(nombre="Evento extremo", puntos=1000)
