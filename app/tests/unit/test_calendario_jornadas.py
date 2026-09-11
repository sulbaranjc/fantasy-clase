"""Pruebas unitarias de `generar_calendario`.

La primera es una prueba de fidelidad: reproduce, jornada a jornada, el
calendario real calculado por las fórmulas de "Fantasy_Clase.xlsx"
(=MIN(B5+13,$B$2)) para la temporada 21/09/2026-05/03/2027, confirmando
que la migración a Python no cambió el comportamiento original.
"""
from datetime import date

from modules.jornadas.service import generar_calendario

CALENDARIO_ORIGINAL_DEL_EXCEL = [
    (1, date(2026, 9, 21), date(2026, 10, 4)),
    (2, date(2026, 10, 5), date(2026, 10, 18)),
    (3, date(2026, 10, 19), date(2026, 11, 1)),
    (4, date(2026, 11, 2), date(2026, 11, 15)),
    (5, date(2026, 11, 16), date(2026, 11, 29)),
    (6, date(2026, 11, 30), date(2026, 12, 13)),
    (7, date(2026, 12, 14), date(2026, 12, 27)),
    (8, date(2026, 12, 28), date(2027, 1, 10)),
    (9, date(2027, 1, 11), date(2027, 1, 24)),
    (10, date(2027, 1, 25), date(2027, 2, 7)),
    (11, date(2027, 2, 8), date(2027, 2, 21)),
    (12, date(2027, 2, 22), date(2027, 3, 5)),
]


def test_reproduce_fielmente_el_calendario_del_excel_original():
    jornadas = generar_calendario(
        fecha_inicio=date(2026, 9, 21), fecha_fin=date(2027, 3, 5),
        duracion_jornada_dias=14, ventana_fichaje_horas=24,
    )

    assert len(jornadas) == 12
    for jornada, (numero, inicio, fin) in zip(jornadas, CALENDARIO_ORIGINAL_DEL_EXCEL):
        assert jornada["numero"] == numero
        assert jornada["fecha_inicio"] == inicio
        assert jornada["fecha_fin"] == fin


def test_la_ultima_jornada_se_recorta_para_no_pasarse_del_fin_de_temporada():
    jornadas = generar_calendario(
        fecha_inicio=date(2026, 9, 21), fecha_fin=date(2027, 3, 5),
        duracion_jornada_dias=14, ventana_fichaje_horas=24,
    )

    ultima = jornadas[-1]
    duracion_dias = (ultima["fecha_fin"] - ultima["fecha_inicio"]).days + 1
    assert duracion_dias == 12  # la última dura menos que las 2 semanas habituales
    assert ultima["fecha_fin"] == date(2027, 3, 5)


def test_ventana_de_fichajes_abre_al_inicio_y_cierra_horas_despues():
    jornadas = generar_calendario(
        fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 10, 4),
        duracion_jornada_dias=14, ventana_fichaje_horas=24,
    )

    jornada = jornadas[0]
    assert jornada["apertura_fichajes"].date() == jornada["fecha_inicio"]
    assert (jornada["cierre_fichajes"] - jornada["apertura_fichajes"]).total_seconds() == 24 * 3600


def test_temporada_mas_corta_que_una_jornada_genera_una_unica_jornada_recortada():
    jornadas = generar_calendario(
        fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 9, 25),
        duracion_jornada_dias=14, ventana_fichaje_horas=24,
    )

    assert len(jornadas) == 1
    assert jornadas[0]["fecha_fin"] == date(2026, 9, 25)
