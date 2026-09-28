"""Pruebas unitarias de las funciones puras de `plantillas/service.py`."""
from datetime import datetime, timedelta

from modules.plantillas.service import (
    companeros_repetidos,
    esta_dentro_de_ventana,
    excede_limite_de_equipos,
    excede_presupuesto,
    manager_esta_incluido,
)


def test_excede_presupuesto_cuando_la_suma_supera_el_limite():
    assert excede_presupuesto([25, 25, 25, 25, 25], 120) is True


def test_no_excede_presupuesto_cuando_la_suma_es_igual_al_limite():
    assert excede_presupuesto([24, 24, 24, 24, 24], 120) is False


def test_no_excede_presupuesto_cuando_la_suma_es_menor():
    assert excede_presupuesto([20, 20, 20, 20, 20], 120) is False


def test_ventana_abierta_en_el_instante_de_apertura_incluido():
    apertura = datetime(2026, 9, 21, 0, 0)
    cierre = apertura + timedelta(hours=24)
    assert esta_dentro_de_ventana(apertura, apertura, cierre) is True


def test_ventana_abierta_en_el_instante_de_cierre_incluido():
    apertura = datetime(2026, 9, 21, 0, 0)
    cierre = apertura + timedelta(hours=24)
    assert esta_dentro_de_ventana(cierre, apertura, cierre) is True


def test_ventana_cerrada_antes_de_la_apertura():
    apertura = datetime(2026, 9, 21, 0, 0)
    cierre = apertura + timedelta(hours=24)
    antes = apertura - timedelta(minutes=1)
    assert esta_dentro_de_ventana(antes, apertura, cierre) is False


def test_ventana_cerrada_despues_del_cierre():
    apertura = datetime(2026, 9, 21, 0, 0)
    cierre = apertura + timedelta(hours=24)
    despues = cierre + timedelta(minutes=1)
    assert esta_dentro_de_ventana(despues, apertura, cierre) is False


def test_manager_incluido_entre_los_jugadores():
    assert manager_esta_incluido(1, [1, 2, 3, 4, 5]) is True


def test_manager_no_incluido_entre_los_jugadores():
    assert manager_esta_incluido(9, [1, 2, 3, 4, 5]) is False


def test_no_excede_el_limite_cuando_aun_queda_hueco():
    # 5 managers ya lo tienen fichado; con el actual serían 6, justo el límite.
    assert excede_limite_de_equipos(veces_fichado=5, limite=6) is False


def test_excede_el_limite_cuando_ya_esta_completo():
    # 6 managers ya lo tienen fichado; con el actual serían 7, supera el límite.
    assert excede_limite_de_equipos(veces_fichado=6, limite=6) is True


def test_no_excede_el_limite_sin_nadie_mas_fichandolo():
    assert excede_limite_de_equipos(veces_fichado=0, limite=1) is False


def test_companeros_repetidos_detecta_solapamiento():
    # manager 1; antes fichó a [2, 3, 4, 5]; ahora repite a 3 y 4.
    repetidos = companeros_repetidos([1, 3, 4, 6, 7], [1, 2, 3, 4, 5], manager_id=1)
    assert repetidos == {3, 4}


def test_companeros_repetidos_vacio_sin_solapamiento():
    repetidos = companeros_repetidos([1, 6, 7, 8, 9], [1, 2, 3, 4, 5], manager_id=1)
    assert repetidos == set()


def test_companeros_repetidos_ignora_al_propio_manager():
    # el manager siempre se repite a sí mismo entre jornadas; no cuenta.
    repetidos = companeros_repetidos([1, 6, 7, 8, 9], [1, 2, 3, 4, 5], manager_id=1)
    assert 1 not in repetidos
