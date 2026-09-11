"""Pruebas unitarias de las funciones puras de `clasificacion/service.py`."""
from modules.clasificacion.service import calcular_puntos_manager, calcular_ranking


def test_calcular_puntos_manager_duplica_la_aportacion_del_capitan():
    puntos_por_jugador = {1: 5, 2: 0, 3: -2, 4: 1, 5: 0}
    total = calcular_puntos_manager(puntos_por_jugador, capitan_id=1)
    # suma (5+0-2+1+0=4) + bonus del capitán (5) = 9
    assert total == 9


def test_calcular_puntos_manager_con_capitan_de_puntos_negativos():
    puntos_por_jugador = {1: 5, 2: -3, 3: 0, 4: 1, 5: 0}
    total = calcular_puntos_manager(puntos_por_jugador, capitan_id=2)
    # suma (5-3+0+1+0=3) + bonus del capitán (-3) = 0
    assert total == 0


def test_calcular_puntos_manager_sin_ningun_punto():
    puntos_por_jugador = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    assert calcular_puntos_manager(puntos_por_jugador, capitan_id=3) == 0


def test_calcular_ranking_ordena_de_mayor_a_menor():
    ranking = calcular_ranking([(1, 10), (2, 30), (3, 20)])
    assert [r["manager_id"] for r in ranking] == [2, 3, 1]
    assert [r["posicion"] for r in ranking] == [1, 2, 3]


def test_calcular_ranking_los_empates_comparten_posicion_y_saltan_el_hueco():
    # Dos managers empatados en 1º puesto: el siguiente debe ser 3º, no 2º.
    ranking = calcular_ranking([(1, 30), (2, 30), (3, 10)])
    posiciones = {r["manager_id"]: r["posicion"] for r in ranking}
    assert posiciones[1] == 1
    assert posiciones[2] == 1
    assert posiciones[3] == 3


def test_calcular_ranking_con_una_sola_entrada():
    ranking = calcular_ranking([(1, 0)])
    assert ranking == [{"manager_id": 1, "puntos_totales": 0, "posicion": 1}]
