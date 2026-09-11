"""Pruebas de integración del módulo catalogo_puntos contra MySQL real.

Todo el módulo queda reservado al profesor dueño de la clase (herramienta
de configuración, no de consulta compartida)."""
import pytest

from .conftest import login_como_alumno


@pytest.mark.asyncio
async def test_crear_evento_y_recuperarlo(cliente, clase_id):
    payload = {"nombre": "Examen >9", "puntos": 6}

    respuesta_creacion = await cliente.post("/catalogo-puntos", params={"clase_id": clase_id}, json=payload)
    assert respuesta_creacion.status_code == 201
    evento = respuesta_creacion.json()
    assert evento["nombre"] == "Examen >9"
    assert evento["puntos"] == 6
    assert evento["activo"] is True

    respuesta_detalle = await cliente.get(f"/catalogo-puntos/{evento['id']}")
    assert respuesta_detalle.status_code == 200
    assert respuesta_detalle.json() == evento


@pytest.mark.asyncio
async def test_no_permite_nombres_duplicados_en_la_misma_clase(cliente, clase_id):
    payload = {"nombre": "Comportamiento disruptivo", "puntos": -2}

    primera = await cliente.post("/catalogo-puntos", params={"clase_id": clase_id}, json=payload)
    assert primera.status_code == 201

    segunda = await cliente.post("/catalogo-puntos", params={"clase_id": clase_id}, json=payload)
    assert segunda.status_code == 409


@pytest.mark.asyncio
async def test_listar_solo_activos_excluye_los_desactivados(cliente, clase_id):
    creado = await cliente.post(
        "/catalogo-puntos", params={"clase_id": clase_id}, json={"nombre": "Ayuda a un compañero", "puntos": 2}
    )
    evento_id = creado.json()["id"]

    await cliente.put(
        f"/catalogo-puntos/{evento_id}",
        json={"nombre": "Ayuda a un compañero", "puntos": 2, "activo": False},
    )

    listado_todos = await cliente.get("/catalogo-puntos", params={"clase_id": clase_id})
    listado_activos = await cliente.get("/catalogo-puntos", params={"clase_id": clase_id, "solo_activos": True})

    ids_todos = [e["id"] for e in listado_todos.json()]
    ids_activos = [e["id"] for e in listado_activos.json()]
    assert evento_id in ids_todos
    assert evento_id not in ids_activos


@pytest.mark.asyncio
async def test_obtener_evento_inexistente_devuelve_404(cliente, profesor_id):
    respuesta = await cliente.get("/catalogo-puntos/999999")
    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_un_alumno_no_puede_ver_ni_crear_en_el_catalogo(cliente, clase_id, alumno_id):
    await login_como_alumno(cliente, alumno_id)

    listado = await cliente.get("/catalogo-puntos", params={"clase_id": clase_id})
    creacion = await cliente.post("/catalogo-puntos", params={"clase_id": clase_id}, json={"nombre": "X", "puntos": 1})

    assert listado.status_code == 403
    assert creacion.status_code == 403


@pytest.mark.asyncio
async def test_requiere_sesion(cliente):
    respuesta = await cliente.get("/catalogo-puntos", params={"clase_id": 1})
    assert respuesta.status_code == 401
