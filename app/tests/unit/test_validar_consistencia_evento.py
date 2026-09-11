"""Pruebas unitarias de `validar_consistencia`: sin base de datos, con
diccionarios armados a mano que imitan lo que devolvería cada repositorio.
"""
import pytest

from modules.eventos.service import (
    AlumnoInvalidoError,
    JornadaInvalidaError,
    TipoEventoInvalidoError,
    validar_consistencia,
)

CLASE_A = 1
CLASE_B = 2

ALUMNO = {"id": 1, "clase_id": CLASE_A}
JORNADA = {"id": 1, "clase_id": CLASE_A}
TIPO_ACTIVO = {"id": 1, "clase_id": CLASE_A, "activo": True}
TIPO_INACTIVO = {"id": 1, "clase_id": CLASE_A, "activo": False}


def test_acepta_una_combinacion_valida():
    validar_consistencia(CLASE_A, ALUMNO, JORNADA, TIPO_ACTIVO)  # no lanza


def test_rechaza_alumno_de_otra_clase():
    alumno_de_otra_clase = {"id": 1, "clase_id": CLASE_B}
    with pytest.raises(AlumnoInvalidoError):
        validar_consistencia(CLASE_A, alumno_de_otra_clase, JORNADA, TIPO_ACTIVO)


def test_rechaza_alumno_inexistente():
    with pytest.raises(AlumnoInvalidoError):
        validar_consistencia(CLASE_A, None, JORNADA, TIPO_ACTIVO)


def test_rechaza_jornada_de_otra_clase():
    jornada_de_otra_clase = {"id": 1, "clase_id": CLASE_B}
    with pytest.raises(JornadaInvalidaError):
        validar_consistencia(CLASE_A, ALUMNO, jornada_de_otra_clase, TIPO_ACTIVO)


def test_rechaza_tipo_de_evento_de_otra_clase():
    tipo_de_otra_clase = {"id": 1, "clase_id": CLASE_B, "activo": True}
    with pytest.raises(TipoEventoInvalidoError):
        validar_consistencia(CLASE_A, ALUMNO, JORNADA, tipo_de_otra_clase)


def test_rechaza_tipo_de_evento_desactivado():
    with pytest.raises(TipoEventoInvalidoError):
        validar_consistencia(CLASE_A, ALUMNO, JORNADA, TIPO_INACTIVO)
