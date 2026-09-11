"""Pruebas unitarias de core/security.py (sin BD ni HTTP)."""
from core.security import hash_password, verify_password


def test_hash_y_verificacion_de_una_contraseña_correcta():
    hash_ = hash_password("mi-contraseña-1234")
    assert verify_password("mi-contraseña-1234", hash_) is True


def test_verificacion_de_una_contraseña_incorrecta():
    hash_ = hash_password("mi-contraseña-1234")
    assert verify_password("otra-contraseña", hash_) is False


def test_verificacion_ante_un_hash_corrupto_no_revienta_devuelve_false():
    # Un password_hash que passlib no reconoce (dato corrupto o sembrado a
    # mano) debe tratarse como credenciales inválidas, nunca como un 500.
    assert verify_password("cualquier-cosa", "esto-no-es-un-hash-bcrypt") is False
