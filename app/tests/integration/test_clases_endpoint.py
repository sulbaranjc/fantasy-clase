"""Pruebas de integración del módulo clases contra MySQL real."""
import pytest


@pytest.mark.asyncio
async def test_crear_clase_y_recuperarla(cliente, profesor_id):
    payload = {
        "nombre": "1º ESO A — curso 2026/2027",
        "fecha_inicio": "2026-09-21",
        "fecha_fin": "2027-03-05",
        "presupuesto_manager": 120,
    }

    respuesta_creacion = await cliente.post("/clases", params={"profesor_id": profesor_id}, json=payload)
    assert respuesta_creacion.status_code == 201
    clase_creada = respuesta_creacion.json()
    assert clase_creada["nombre"] == payload["nombre"]
    assert clase_creada["profesor_id"] == profesor_id
    # Valores por defecto de la regla de negocio, no enviados en el payload.
    assert clase_creada["valor_inicial_jugador"] == 20
    assert clase_creada["valor_minimo_jugador"] == 10

    respuesta_detalle = await cliente.get(f"/clases/{clase_creada['id']}")
    assert respuesta_detalle.status_code == 200
    assert respuesta_detalle.json() == clase_creada

    respuesta_listado = await cliente.get("/clases", params={"profesor_id": profesor_id})
    assert respuesta_listado.status_code == 200
    ids_listados = [c["id"] for c in respuesta_listado.json()]
    assert clase_creada["id"] in ids_listados


@pytest.mark.asyncio
async def test_rechaza_fecha_fin_anterior_a_fecha_inicio(cliente, profesor_id):
    payload = {
        "nombre": "Clase con fechas inválidas",
        "fecha_inicio": "2026-09-21",
        "fecha_fin": "2026-01-01",
    }

    respuesta = await cliente.post("/clases", params={"profesor_id": profesor_id}, json=payload)

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_obtener_clase_inexistente_devuelve_404(cliente):
    respuesta = await cliente.get("/clases/999999")

    assert respuesta.status_code == 404
