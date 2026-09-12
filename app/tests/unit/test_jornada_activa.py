"""Pruebas unitarias de `obtener_jornada_con_ventana_abierta` (sin BD):
localiza, de una lista de jornadas, la que tiene ventana de fichajes
abierta en un instante dado."""
from datetime import datetime

from modules.jornadas.service import obtener_jornada_con_ventana_abierta

JORNADA_1 = {
    "numero": 1,
    "apertura_fichajes": datetime(2026, 9, 21, 0, 0),
    "cierre_fichajes": datetime(2026, 9, 22, 0, 0),
}
JORNADA_2 = {
    "numero": 2,
    "apertura_fichajes": datetime(2026, 10, 5, 0, 0),
    "cierre_fichajes": datetime(2026, 10, 6, 0, 0),
}


def test_encuentra_la_jornada_cuya_ventana_esta_abierta():
    ahora = datetime(2026, 9, 21, 12, 0)
    resultado = obtener_jornada_con_ventana_abierta([JORNADA_1, JORNADA_2], ahora)
    assert resultado["numero"] == 1


def test_devuelve_none_si_ninguna_ventana_esta_abierta():
    ahora = datetime(2026, 9, 25, 0, 0)  # entre las dos ventanas
    assert obtener_jornada_con_ventana_abierta([JORNADA_1, JORNADA_2], ahora) is None


def test_devuelve_none_con_lista_vacia():
    assert obtener_jornada_con_ventana_abierta([], datetime.now()) is None
