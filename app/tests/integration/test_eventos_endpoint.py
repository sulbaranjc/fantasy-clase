"""Pruebas de integración del módulo eventos contra MySQL real."""
from datetime import date

import pytest

from core.database import get_pool
from core.security import hash_password
from modules.alumnos import repository as alumnos_repository
from modules.clases import repository as clases_repository
from modules.jornadas import repository as jornadas_repository

from .conftest import login_como_alumno, login_como_profesor


@pytest.mark.asyncio
async def test_crear_evento_copia_los_puntos_vigentes_del_catalogo(
    cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id
):
    payload = {
        "alumno_id": alumno_id,
        "jornada_id": jornada_id,
        "catalogo_punto_id": catalogo_punto_id,
        "fecha": "2026-09-22",
        "nota_numerica": 8.5,
        "comentario": "Buena participación",
    }

    respuesta = await cliente.post("/eventos", params={"clase_id": clase_id}, json=payload)

    assert respuesta.status_code == 201
    evento = respuesta.json()
    assert evento["puntos_otorgados"] == 5  # puntos del "Evento de prueba" (fixture)
    assert evento["nota_numerica"] == 8.5
    assert evento["comentario"] == "Buena participación"


@pytest.mark.asyncio
async def test_rechaza_alumno_de_otra_clase(cliente, clase_id, jornada_id, catalogo_punto_id, profesor_id):
    # Un alumno que existe, pero pertenece a una clase distinta.
    pool = get_pool()
    otra_clase_id = await clases_repository.crear(
        pool, profesor_id=profesor_id, nombre="Otra clase", fecha_inicio=date(2026, 9, 21),
        fecha_fin=date(2027, 3, 5), duracion_jornada_dias=14, ventana_fichaje_horas=24,
        valor_inicial_jugador=20, valor_minimo_jugador=10, factor_recalculo_valor=0.10,
        presupuesto_manager=120,
    )
    alumno_de_otra_clase = await alumnos_repository.crear(
        pool, otra_clase_id, "Alumno ajeno", "alumno_ajeno_test", hash_password("x"), 20
    )

    payload = {
        "alumno_id": alumno_de_otra_clase,
        "jornada_id": jornada_id,
        "catalogo_punto_id": catalogo_punto_id,
        "fecha": "2026-09-22",
    }
    respuesta = await cliente.post("/eventos", params={"clase_id": clase_id}, json=payload)

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_rechaza_tipo_de_evento_desactivado(cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id):
    await cliente.put(
        f"/catalogo-puntos/{catalogo_punto_id}",
        json={"nombre": "Evento de prueba", "puntos": 5, "activo": False},
    )

    payload = {
        "alumno_id": alumno_id, "jornada_id": jornada_id,
        "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22",
    }
    respuesta = await cliente.post("/eventos", params={"clase_id": clase_id}, json=payload)

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_actualizar_evento_recalcula_los_puntos_otorgados(
    cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id
):
    creado = await cliente.post(
        "/eventos", params={"clase_id": clase_id},
        json={"alumno_id": alumno_id, "jornada_id": jornada_id,
              "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22"},
    )
    evento_id = creado.json()["id"]

    otro_tipo = await cliente.post(
        "/catalogo-puntos", params={"clase_id": clase_id},
        json={"nombre": "Otro tipo de evento", "puntos": -3},
    )
    otro_tipo_id = otro_tipo.json()["id"]

    actualizado = await cliente.put(
        f"/eventos/{evento_id}",
        json={"catalogo_punto_id": otro_tipo_id, "fecha": "2026-09-23", "comentario": "Corregido"},
    )

    assert actualizado.status_code == 200
    assert actualizado.json()["puntos_otorgados"] == -3
    assert actualizado.json()["comentario"] == "Corregido"


@pytest.mark.asyncio
async def test_eliminar_evento(cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id):
    creado = await cliente.post(
        "/eventos", params={"clase_id": clase_id},
        json={"alumno_id": alumno_id, "jornada_id": jornada_id,
              "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22"},
    )
    evento_id = creado.json()["id"]

    eliminado = await cliente.delete(f"/eventos/{evento_id}")
    assert eliminado.status_code == 204

    respuesta = await cliente.get(f"/eventos/{evento_id}")
    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_listar_eventos_de_alumno_y_de_jornada(
    cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id
):
    await cliente.post(
        "/eventos", params={"clase_id": clase_id},
        json={"alumno_id": alumno_id, "jornada_id": jornada_id,
              "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22"},
    )

    por_alumno = await cliente.get(f"/eventos/alumno/{alumno_id}")
    por_jornada = await cliente.get(f"/eventos/jornada/{jornada_id}")

    assert por_alumno.status_code == 200 and len(por_alumno.json()) == 1
    assert por_jornada.status_code == 200 and len(por_jornada.json()) == 1


@pytest.mark.asyncio
async def test_un_alumno_puede_ver_su_propio_historial(
    cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id
):
    await cliente.post(
        "/eventos", params={"clase_id": clase_id},
        json={"alumno_id": alumno_id, "jornada_id": jornada_id,
              "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22"},
    )

    await login_como_alumno(cliente, alumno_id)
    respuesta = await cliente.get(f"/eventos/alumno/{alumno_id}")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


@pytest.mark.asyncio
async def test_un_alumno_no_puede_ver_el_historial_de_otro(cliente, clase_id, cinco_alumnos_ids):
    await login_como_alumno(cliente, cinco_alumnos_ids[0])

    respuesta = await cliente.get(f"/eventos/alumno/{cinco_alumnos_ids[1]}")

    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_un_alumno_no_puede_ver_eventos_por_jornada_ni_crear(
    cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id
):
    await login_como_alumno(cliente, alumno_id)

    listado = await cliente.get(f"/eventos/jornada/{jornada_id}")
    creacion = await cliente.post(
        "/eventos", params={"clase_id": clase_id},
        json={"alumno_id": alumno_id, "jornada_id": jornada_id,
              "catalogo_punto_id": catalogo_punto_id, "fecha": "2026-09-22"},
    )

    assert listado.status_code == 403
    assert creacion.status_code == 403


@pytest.mark.asyncio
async def test_importar_eventos_desde_archivo(
    cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id, profesor_id
):
    pool = get_pool()
    alumno = await alumnos_repository.obtener_por_id(pool, alumno_id)
    jornada = await jornadas_repository.obtener_por_id(pool, jornada_id)

    contenido = (
        "jornada;alumno;categoria;fecha\n"
        f"{jornada['numero']};{alumno['username']};Evento de prueba;2026-09-22\n"
    )

    respuesta = await cliente.post(
        "/eventos/importar", params={"clase_id": clase_id},
        files={"archivo": ("eventos.txt", contenido, "text/plain")},
    )

    assert respuesta.status_code == 201
    creados = respuesta.json()
    assert len(creados) == 1
    assert creados[0]["alumno_id"] == alumno_id
    assert creados[0]["jornada_id"] == jornada_id
    assert creados[0]["puntos_otorgados"] == 5


@pytest.mark.asyncio
async def test_importar_eventos_rechaza_alumno_inexistente(cliente, clase_id, jornada_id, profesor_id):
    pool = get_pool()
    jornada = await jornadas_repository.obtener_por_id(pool, jornada_id)
    contenido = f"{jornada['numero']};no_existe_este_usuario;Evento de prueba;2026-09-22\n"

    respuesta = await cliente.post(
        "/eventos/importar", params={"clase_id": clase_id},
        files={"archivo": ("eventos.txt", contenido, "text/plain")},
    )

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_importar_eventos_rechaza_categoria_inexistente(cliente, clase_id, alumno_id, jornada_id, profesor_id):
    pool = get_pool()
    alumno = await alumnos_repository.obtener_por_id(pool, alumno_id)
    jornada = await jornadas_repository.obtener_por_id(pool, jornada_id)
    contenido = f"{jornada['numero']};{alumno['username']};Categoria inexistente;2026-09-22\n"

    respuesta = await cliente.post(
        "/eventos/importar", params={"clase_id": clase_id},
        files={"archivo": ("eventos.txt", contenido, "text/plain")},
    )

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_importar_eventos_no_crea_nada_si_una_fila_falla(
    cliente, clase_id, alumno_id, jornada_id, catalogo_punto_id, profesor_id
):
    # Todo o nada: la primera fila es válida, la segunda referencia un
    # alumno inexistente -> no debe crearse ni siquiera la primera.
    pool = get_pool()
    alumno = await alumnos_repository.obtener_por_id(pool, alumno_id)
    jornada = await jornadas_repository.obtener_por_id(pool, jornada_id)
    contenido = (
        f"{jornada['numero']};{alumno['username']};Evento de prueba;2026-09-22\n"
        f"{jornada['numero']};no_existe_este_usuario;Evento de prueba;2026-09-22\n"
    )

    respuesta = await cliente.post(
        "/eventos/importar", params={"clase_id": clase_id},
        files={"archivo": ("eventos.txt", contenido, "text/plain")},
    )
    assert respuesta.status_code == 422

    historial = await cliente.get(f"/eventos/alumno/{alumno_id}")
    assert historial.json() == []


@pytest.mark.asyncio
async def test_un_alumno_no_puede_importar_eventos(cliente, clase_id, alumno_id):
    await login_como_alumno(cliente, alumno_id)

    respuesta = await cliente.post(
        "/eventos/importar", params={"clase_id": clase_id},
        files={"archivo": ("eventos.txt", "1;x;y;2026-09-22\n", "text/plain")},
    )

    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_requiere_sesion(cliente):
    respuesta = await cliente.get("/eventos/alumno/1")
    assert respuesta.status_code == 401
