"""Pruebas de integración del módulo auth contra MySQL real.

`cliente` (httpx.AsyncClient) conserva las cookies entre peticiones dentro
del mismo test, igual que haría un navegador: login -> /me -> logout.
"""
import pytest


@pytest.mark.asyncio
async def test_login_profesor_correcto_fija_cookie_y_devuelve_al_usuario(cliente, profesor_con_password):
    respuesta = await cliente.post(
        "/auth/profesor/login",
        json={"username": profesor_con_password["username"], "password": profesor_con_password["password"]},
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "tipo": "profesor", "id": profesor_con_password["id"],
        "nombre": "Profesor de login", "clase_id": None,
    }
    assert "fantasy_session" in respuesta.cookies


@pytest.mark.asyncio
async def test_login_profesor_password_incorrecta_devuelve_401(cliente, profesor_con_password):
    respuesta = await cliente.post(
        "/auth/profesor/login",
        json={"username": profesor_con_password["username"], "password": "otra-cosa"},
    )
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_login_profesor_usuario_inexistente_devuelve_401(cliente):
    respuesta = await cliente.post(
        "/auth/profesor/login", json={"username": "no-existe", "password": "lo-que-sea"}
    )
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_login_alumno_correcto(cliente, alumno_con_password):
    respuesta = await cliente.post(
        "/auth/alumno/login",
        json={"username": alumno_con_password["username"], "password": alumno_con_password["password"]},
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "tipo": "alumno", "id": alumno_con_password["id"],
        "nombre": "Alumno de login", "clase_id": alumno_con_password["clase_id"],
    }


@pytest.mark.asyncio
async def test_me_sin_sesion_devuelve_401(cliente):
    respuesta = await cliente.get("/auth/me")
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_flujo_completo_login_me_logout(cliente, alumno_con_password):
    login = await cliente.post(
        "/auth/alumno/login",
        json={"username": alumno_con_password["username"], "password": alumno_con_password["password"]},
    )
    assert login.status_code == 200

    me = await cliente.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == alumno_con_password["id"]

    logout = await cliente.post("/auth/logout")
    assert logout.status_code == 200

    me_despues = await cliente.get("/auth/me")
    assert me_despues.status_code == 401
