"""Pruebas unitarias de la regla de negocio más específica del proyecto:
el recálculo del valor de mercado de un jugador al cierre de cada jornada.

No dependen de base de datos ni de FastAPI: solo prueban la función pura,
que es justo el objetivo de separar la lógica de negocio en `service.py`.
"""
from modules.alumnos.service import recalcular_valor

FACTOR = 0.10
VALOR_MINIMO = 10


def test_jornada_positiva_sube_el_valor_redondeando_hacia_abajo():
    # 8 puntos * 0.10 = 0.8 -> floor = 0 -> el valor no cambia
    assert recalcular_valor(20, 8, FACTOR, VALOR_MINIMO) == 20


def test_jornada_muy_positiva_sube_el_valor():
    # 25 puntos * 0.10 = 2.5 -> floor = 2
    assert recalcular_valor(20, 25, FACTOR, VALOR_MINIMO) == 22


def test_jornada_negativa_baja_el_valor():
    # -12 puntos * 0.10 = -1.2 -> floor = -2 (floor redondea hacia -inf)
    assert recalcular_valor(20, -12, FACTOR, VALOR_MINIMO) == 18


def test_el_valor_nunca_baja_del_minimo():
    assert recalcular_valor(11, -50, FACTOR, VALOR_MINIMO) == VALOR_MINIMO


def test_jornada_sin_eventos_no_cambia_el_valor():
    assert recalcular_valor(20, 0, FACTOR, VALOR_MINIMO) == 20
