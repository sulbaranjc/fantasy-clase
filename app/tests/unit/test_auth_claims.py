"""Pruebas unitarias de `usuario_desde_claims` (sin BD ni HTTP): reconstruye
el usuario autenticado a partir de los claims ya decodificados de un JWT."""
from modules.auth.service import usuario_desde_claims


def test_reconstruye_un_profesor_desde_los_claims():
    claims = {"sub": "profesor:7", "nombre": "Álvaro"}
    usuario = usuario_desde_claims(claims)
    assert usuario == {"tipo": "profesor", "id": 7, "nombre": "Álvaro", "clase_id": None}


def test_reconstruye_un_alumno_desde_los_claims():
    claims = {"sub": "alumno:42", "nombre": "María", "clase_id": 3}
    usuario = usuario_desde_claims(claims)
    assert usuario == {"tipo": "alumno", "id": 42, "nombre": "María", "clase_id": 3}
