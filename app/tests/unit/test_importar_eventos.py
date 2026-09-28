"""Pruebas unitarias de `parsear_archivo_eventos`: sin base de datos, solo
sobre el formato del texto del archivo."""
import pytest
from datetime import date

from modules.eventos.service import ImportacionInvalidaError, parsear_archivo_eventos


def test_parsea_varias_lineas_validas():
    contenido = (
        "3;ana;Examen aprobado;2026-10-05\n"
        "3;bruno;Participacion en clase;2026-10-05\n"
    )
    filas = parsear_archivo_eventos(contenido)
    assert len(filas) == 2
    assert filas[0] == {
        "numero_linea": 1, "numero_jornada": 3, "username_alumno": "ana",
        "nombre_categoria": "Examen aprobado", "fecha": date(2026, 10, 5),
    }
    assert filas[1]["username_alumno"] == "bruno"


def test_ignora_lineas_vacias():
    contenido = "3;ana;Examen aprobado;2026-10-05\n\n\n"
    filas = parsear_archivo_eventos(contenido)
    assert len(filas) == 1


def test_descarta_la_cabecera_opcional():
    contenido = (
        "jornada;alumno;categoria;fecha\n"
        "3;ana;Examen aprobado;2026-10-05\n"
    )
    filas = parsear_archivo_eventos(contenido)
    assert len(filas) == 1
    assert filas[0]["numero_jornada"] == 3


def test_sin_cabecera_la_primera_linea_tambien_se_procesa():
    contenido = "3;ana;Examen aprobado;2026-10-05\n"
    filas = parsear_archivo_eventos(contenido)
    assert len(filas) == 1


def test_rechaza_linea_con_numero_de_campos_incorrecto():
    with pytest.raises(ImportacionInvalidaError):
        parsear_archivo_eventos("3;ana;Examen aprobado\n")


def test_rechaza_jornada_no_numerica():
    with pytest.raises(ImportacionInvalidaError):
        parsear_archivo_eventos("tres;ana;Examen aprobado;2026-10-05\n")


def test_rechaza_fecha_invalida():
    with pytest.raises(ImportacionInvalidaError):
        parsear_archivo_eventos("3;ana;Examen aprobado;05-10-2026\n")
