"""Fixtures compartidas por las pruebas de integración.

Todas ejercitan la app real (lifespan real -> pool de MySQL real) contra la
base de datos del propio docker-compose de desarrollo.
"""
import uuid
from datetime import date, datetime, timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.database import get_pool
from core.security import hash_password
from main import app
from modules.alumnos import repository as alumnos_repository
from modules.catalogo_puntos import repository as catalogo_repository
from modules.clases import repository as clases_repository
from modules.jornadas import repository as jornadas_repository
from modules.jornadas import service as jornadas_service
from modules.profesores import repository as profesores_repository

# Contraseñas conocidas fijas para las cuentas de prueba: los tests de
# endpoints protegidos necesitan poder iniciar sesión de verdad, no solo
# tener un id. Nunca se usan fuera de la base de datos de pruebas.
PASSWORD_PROFESOR_PRUEBA = "clave-super-segura"
PASSWORD_ALUMNOS_PRUEBA = "clave-alumno-1234"


@pytest_asyncio.fixture
async def cliente():
    """Cliente HTTP async contra la app, con su lifespan (pool de MySQL)
    activo durante todo el test. Conserva cookies entre peticiones, igual
    que un navegador, así que un login dentro del test (o en una fixture
    de la que dependa) deja la sesión activa para el resto de llamadas."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


async def login_como_alumno(cliente: AsyncClient, alumno_id: int) -> None:
    """Cambia la sesión del `cliente` a la de un alumno de prueba ya
    creado con `PASSWORD_ALUMNOS_PRUEBA` (fixtures `alumno_id` o
    `cinco_alumnos_ids`). Útil quien vaya a fichar debe ser el propio
    alumno autenticado, no el profesor con el que arrancó el test."""
    alumno = await alumnos_repository.obtener_por_id(get_pool(), alumno_id)
    respuesta = await cliente.post(
        "/auth/alumno/login", json={"username": alumno["username"], "password": PASSWORD_ALUMNOS_PRUEBA}
    )
    assert respuesta.status_code == 200, respuesta.text


async def login_como_profesor(cliente: AsyncClient, profesor_id: int) -> None:
    """Cambia la sesión del `cliente` a la del profesor de prueba
    identificado por `profesor_id` (fixture `profesor_id`). Útil tras
    haber cambiado la sesión a un alumno (`login_como_alumno`) y necesitar
    volver a operar como el profesor dentro del mismo test."""
    profesor = await profesores_repository.obtener_por_id(get_pool(), profesor_id)
    respuesta = await cliente.post(
        "/auth/profesor/login", json={"username": profesor["username"], "password": PASSWORD_PROFESOR_PRUEBA}
    )
    assert respuesta.status_code == 200, respuesta.text


@pytest_asyncio.fixture
async def profesor_id(cliente):
    """Inserta un profesor de prueba con una contraseña conocida e inicia
    sesión con él en el `cliente` compartido: cualquier test que dependa
    de esta fixture (directa o transitivamente, vía `clase_id` y todo lo
    que cuelga de ella) ya tiene una sesión de profesor activa sin tener
    que hacer login explícito.
    """
    pool = get_pool()
    username = f"profesor_test_{uuid.uuid4().hex[:12]}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO profesores (nombre, username, password_hash) VALUES (%s, %s, %s)",
                ("Profesor de prueba", username, hash_password(PASSWORD_PROFESOR_PRUEBA)),
            )
            nuevo_id = cur.lastrowid

    respuesta = await cliente.post(
        "/auth/profesor/login", json={"username": username, "password": PASSWORD_PROFESOR_PRUEBA}
    )
    assert respuesta.status_code == 200, respuesta.text

    yield nuevo_id

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM profesores WHERE id = %s", (nuevo_id,))


@pytest_asyncio.fixture
async def clase_id(profesor_id):
    """Crea una clase de prueba (a través del propio módulo `clases`, no
    con SQL a mano) para los módulos que dependen de una clase existente
    (catalogo_puntos, jornadas, eventos, plantillas...).

    No hace falta limpiarla explícitamente: al borrar el profesor de
    prueba, la cascada de la base de datos se lleva también sus clases.
    """
    pool = get_pool()
    nuevo_id = await clases_repository.crear(
        pool,
        profesor_id=profesor_id,
        nombre="Clase de prueba",
        fecha_inicio=date(2026, 9, 21),
        fecha_fin=date(2027, 3, 5),
        duracion_jornada_dias=14,
        ventana_fichaje_horas=24,
        valor_inicial_jugador=20,
        valor_minimo_jugador=10,
        factor_recalculo_valor=0.10,
        presupuesto_manager=120,
    )
    return nuevo_id


@pytest_asyncio.fixture
async def alumno_id(clase_id):
    """Crea un alumno de prueba en la clase, para los módulos que dependen
    de un alumno existente (eventos, plantillas...)."""
    pool = get_pool()
    username = f"alumno_test_{uuid.uuid4().hex[:12]}"
    return await alumnos_repository.crear(
        pool, clase_id, "Alumno de prueba", username, hash_password(PASSWORD_ALUMNOS_PRUEBA), 20
    )


@pytest_asyncio.fixture
async def catalogo_punto_id(clase_id):
    """Crea un tipo de evento de prueba en la clase, para los módulos que
    dependen de una entrada del catálogo de puntos (eventos...)."""
    pool = get_pool()
    return await catalogo_repository.crear(pool, clase_id, "Evento de prueba", 5)


@pytest_asyncio.fixture
async def jornada_id(clase_id):
    """Genera el calendario de la clase de prueba y devuelve el id de su
    primera jornada, para los módulos que dependen de una jornada existente
    (eventos, plantillas...)."""
    pool = get_pool()
    jornadas = await jornadas_service.generar_y_guardar_calendario(pool, clase_id)
    return jornadas[0]["id"]


@pytest_asyncio.fixture
async def jornada_abierta_id(clase_id):
    """Jornada de prueba cuya ventana de fichajes está abierta *ahora*.

    La fixture `jornada_id` usa el calendario real de la clase (fechas de
    la temporada 2026/2027 de Fantasy_Clase.xlsx), cuya primera ventana
    puede no coincidir con el instante en que corren las pruebas. Los
    módulos que necesitan probar el "camino feliz" de un fichaje dentro
    de plazo usan esta en su lugar; el número de jornada (99) se elige
    fuera del rango 1-12 para no chocar si el mismo test también genera
    el calendario completo.
    """
    pool = get_pool()
    ahora = datetime.now()
    await jornadas_repository.crear_lote(pool, clase_id, [{
        "numero": 99,
        "fecha_inicio": ahora.date(),
        "fecha_fin": ahora.date(),
        "apertura_fichajes": ahora - timedelta(hours=1),
        "cierre_fichajes": ahora + timedelta(hours=1),
    }])
    jornadas = await jornadas_repository.listar_por_clase(pool, clase_id)
    return next(j["id"] for j in jornadas if j["numero"] == 99)


@pytest_asyncio.fixture
async def profesor_con_password(cliente):
    """Como `profesor_id`, pero SIN iniciar sesión automáticamente: para
    los propios tests de auth, que necesitan las credenciales en texto
    plano y probar ellos mismos el login."""
    pool = get_pool()
    username = f"profesor_login_test_{uuid.uuid4().hex[:12]}"
    nuevo_id = await profesores_repository.crear(
        pool, "Profesor de login", username, hash_password(PASSWORD_PROFESOR_PRUEBA)
    )

    yield {"id": nuevo_id, "username": username, "password": PASSWORD_PROFESOR_PRUEBA}

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM profesores WHERE id = %s", (nuevo_id,))


@pytest_asyncio.fixture
async def alumno_con_password(clase_id):
    """Como `alumno_id`, pero exponiendo también sus credenciales: para
    los propios tests de auth, que necesitan probar ellos mismos el login
    (en vez de partir de una sesión ya iniciada)."""
    pool = get_pool()
    username = f"alumno_login_test_{uuid.uuid4().hex[:12]}"
    nuevo_id = await alumnos_repository.crear(
        pool, clase_id, "Alumno de login", username, hash_password(PASSWORD_ALUMNOS_PRUEBA), 20
    )
    return {"id": nuevo_id, "clase_id": clase_id, "username": username, "password": PASSWORD_ALUMNOS_PRUEBA}


@pytest_asyncio.fixture
async def cinco_alumnos_ids(clase_id):
    """Cinco alumnos de prueba en la clase, para fichar una plantilla
    completa (jugadores + manager, que es uno de ellos)."""
    pool = get_pool()
    ids = []
    for _ in range(5):
        username = f"jugador_test_{uuid.uuid4().hex[:12]}"
        nuevo_id = await alumnos_repository.crear(
            pool, clase_id, "Jugador de prueba", username, hash_password(PASSWORD_ALUMNOS_PRUEBA), 20
        )
        ids.append(nuevo_id)
    return ids
