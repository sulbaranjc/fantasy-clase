"""Pruebas unitarias de las reglas de validación de ClaseCreate.

Pydantic es la única fuente de verdad de validación de datos del proyecto;
estas pruebas comprueban esa capa de forma aislada, sin red ni base de datos.
"""
import pytest
from pydantic import ValidationError

from modules.clases.schemas import ClaseCreate

DATOS_VALIDOS = {
    "nombre": "1º ESO A",
    "fecha_inicio": "2026-09-21",
    "fecha_fin": "2027-03-05",
}


def test_acepta_datos_validos_y_aplica_los_valores_por_defecto():
    clase = ClaseCreate(**DATOS_VALIDOS)

    assert clase.valor_inicial_jugador == 20
    assert clase.valor_minimo_jugador == 10
    assert clase.presupuesto_manager == 120
    assert clase.factor_recalculo_valor == 0.10


def test_rechaza_fecha_fin_anterior_o_igual_a_fecha_inicio():
    with pytest.raises(ValidationError):
        ClaseCreate(**{**DATOS_VALIDOS, "fecha_fin": "2026-09-21"})


def test_rechaza_valor_minimo_mayor_que_valor_inicial():
    with pytest.raises(ValidationError):
        ClaseCreate(**{**DATOS_VALIDOS, "valor_inicial_jugador": 15, "valor_minimo_jugador": 20})


def test_rechaza_nombre_vacio():
    with pytest.raises(ValidationError):
        ClaseCreate(**{**DATOS_VALIDOS, "nombre": ""})
