"""Lógica de negocio del módulo eventos.

`validar_consistencia` es la función pura (sin FastAPI ni SQL) que decide
si un evento tiene sentido: que el alumno, la jornada y el tipo de evento
pertenezcan todos a la misma clase, y que el tipo de evento siga activo.
Se cubre con pruebas unitarias que no tocan la base de datos.
"""
from datetime import date

import asyncmy

from modules.alumnos import repository as alumnos_repository
from modules.catalogo_puntos import repository as catalogo_repository
from modules.eventos import repository
from modules.eventos.schemas import EventoCreate, EventoUpdate
from modules.jornadas import repository as jornadas_repository


class AlumnoInvalidoError(Exception):
    """El alumno no existe o no pertenece a la clase del evento."""


class JornadaInvalidaError(Exception):
    """La jornada no existe o no pertenece a la clase del evento."""


class TipoEventoInvalidoError(Exception):
    """El tipo de evento no existe, no pertenece a la clase, o está inactivo."""


class EventoInexistenteError(Exception):
    """No existe el evento sobre el que se intenta operar."""


class ImportacionInvalidaError(Exception):
    """El archivo de importación de eventos tiene un error de formato, o
    alguna de sus filas referencia una jornada/alumno/categoría que no
    existe en esta clase. El mensaje señala la línea exacta del archivo."""


def validar_consistencia(clase_id: int, alumno: dict | None, jornada: dict | None,
                          catalogo_punto: dict | None) -> None:
    if alumno is None or alumno["clase_id"] != clase_id:
        raise AlumnoInvalidoError("El alumno no pertenece a esta clase.")
    if jornada is None or jornada["clase_id"] != clase_id:
        raise JornadaInvalidaError("La jornada no pertenece a esta clase.")
    if catalogo_punto is None or catalogo_punto["clase_id"] != clase_id:
        raise TipoEventoInvalidoError("El tipo de evento no pertenece a esta clase.")
    if not catalogo_punto["activo"]:
        raise TipoEventoInvalidoError("Este tipo de evento está desactivado.")


async def crear_evento(pool: asyncmy.Pool, clase_id: int, datos: EventoCreate) -> int:
    alumno = await alumnos_repository.obtener_por_id(pool, datos.alumno_id)
    jornada = await jornadas_repository.obtener_por_id(pool, datos.jornada_id)
    catalogo_punto = await catalogo_repository.obtener_por_id(pool, datos.catalogo_punto_id)
    validar_consistencia(clase_id, alumno, jornada, catalogo_punto)

    return await repository.crear(
        pool, clase_id, datos.alumno_id, datos.jornada_id, datos.catalogo_punto_id,
        datos.fecha, datos.nota_numerica, datos.comentario, catalogo_punto["puntos"],
    )


async def actualizar_evento(pool: asyncmy.Pool, evento_id: int, datos: EventoUpdate) -> None:
    evento = await repository.obtener_por_id(pool, evento_id)
    if evento is None:
        raise EventoInexistenteError(f"No existe el evento {evento_id}.")

    catalogo_punto = await catalogo_repository.obtener_por_id(pool, datos.catalogo_punto_id)
    if catalogo_punto is None or catalogo_punto["clase_id"] != evento["clase_id"]:
        raise TipoEventoInvalidoError("El tipo de evento no pertenece a esta clase.")
    if not catalogo_punto["activo"]:
        raise TipoEventoInvalidoError("Este tipo de evento está desactivado.")

    # Corregir un evento de una jornada ya cerrada es una edición retroactiva:
    # el recálculo en cascada del valor de mercado y la clasificación se
    # dispara desde el módulo de jornadas/clasificación cuando exista.
    await repository.actualizar(
        pool, evento_id, datos.catalogo_punto_id, datos.fecha,
        datos.nota_numerica, datos.comentario, catalogo_punto["puntos"],
    )


async def eliminar_evento(pool: asyncmy.Pool, evento_id: int) -> None:
    await repository.eliminar(pool, evento_id)


async def obtener_evento(pool: asyncmy.Pool, evento_id: int) -> dict | None:
    return await repository.obtener_por_id(pool, evento_id)


async def listar_eventos_de_alumno(pool: asyncmy.Pool, alumno_id: int) -> list[dict]:
    return await repository.listar_por_alumno(pool, alumno_id)


async def listar_eventos_de_jornada(pool: asyncmy.Pool, jornada_id: int) -> list[dict]:
    return await repository.listar_por_jornada(pool, jornada_id)


def parsear_archivo_eventos(contenido: str) -> list[dict]:
    """Convierte el texto de un archivo de importación en una lista de
    filas a crear. Formato esperado, una línea por evento:

        jornada;alumno;categoria;fecha

    donde `alumno` es su username y `categoria` el nombre exacto de una
    entrada del catálogo de puntos de la clase (así el sistema toma los
    puntos de ahí, igual que un evento creado a mano — nunca un número de
    puntos libre). La primera línea puede ser una cabecera opcional (se
    descarta si su primer campo es literalmente "jornada").

    Función pura: solo valida el formato de cada línea: no comprueba
    todavía que la jornada/alumno/categoría existan de verdad (eso
    requiere la base de datos y lo hace `importar_eventos_desde_archivo`).
    """
    filas = []
    lineas = [linea.strip() for linea in contenido.splitlines() if linea.strip()]
    for numero_linea, linea in enumerate(lineas, start=1):
        campos = [c.strip() for c in linea.split(";")]
        if numero_linea == 1 and campos[0].lower() == "jornada":
            continue

        if len(campos) != 4:
            raise ImportacionInvalidaError(
                f"Línea {numero_linea}: se esperaban 4 campos "
                f"(jornada;alumno;categoria;fecha), hay {len(campos)}."
            )

        numero_jornada_str, username_alumno, nombre_categoria, fecha_str = campos
        if not numero_jornada_str.isdigit():
            raise ImportacionInvalidaError(
                f"Línea {numero_linea}: '{numero_jornada_str}' no es un número de jornada válido."
            )
        try:
            fecha = date.fromisoformat(fecha_str)
        except ValueError:
            raise ImportacionInvalidaError(
                f"Línea {numero_linea}: '{fecha_str}' no es una fecha válida (usa AAAA-MM-DD)."
            ) from None

        filas.append({
            "numero_linea": numero_linea, "numero_jornada": int(numero_jornada_str),
            "username_alumno": username_alumno, "nombre_categoria": nombre_categoria, "fecha": fecha,
        })
    return filas


async def importar_eventos_desde_archivo(pool: asyncmy.Pool, clase_id: int, contenido: str) -> list[int]:
    """Crea en bloque los eventos descritos en el archivo. Todo o nada: si
    cualquier fila referencia una jornada, alumno o categoría que no
    existe en esta clase, no se crea ningún evento — se avisa con el
    detalle exacto de la primera fila problemática, para que se corrija el
    archivo y se reintente completo."""
    filas = parsear_archivo_eventos(contenido)
    catalogo = await catalogo_repository.listar_por_clase(pool, clase_id, solo_activos=False)
    catalogo_por_nombre = {c["nombre"]: c for c in catalogo}

    eventos_a_crear = []
    for fila in filas:
        jornada = await jornadas_repository.obtener_por_clase_y_numero(pool, clase_id, fila["numero_jornada"])
        if jornada is None:
            raise ImportacionInvalidaError(
                f"Línea {fila['numero_linea']}: no existe la jornada {fila['numero_jornada']} en esta clase."
            )

        alumno = await alumnos_repository.obtener_por_username(pool, fila["username_alumno"])
        if alumno is None or alumno["clase_id"] != clase_id:
            raise ImportacionInvalidaError(
                f"Línea {fila['numero_linea']}: el alumno '{fila['username_alumno']}' no existe en esta clase."
            )

        catalogo_punto = catalogo_por_nombre.get(fila["nombre_categoria"])
        if catalogo_punto is None:
            raise ImportacionInvalidaError(
                f"Línea {fila['numero_linea']}: no existe la categoría "
                f"'{fila['nombre_categoria']}' en el catálogo de puntos de esta clase."
            )

        eventos_a_crear.append(
            (alumno["id"], jornada["id"], catalogo_punto["id"], fila["fecha"], catalogo_punto["puntos"])
        )

    ids_creados = []
    for alumno_id, jornada_id, catalogo_punto_id, fecha, puntos in eventos_a_crear:
        evento_id = await repository.crear(
            pool, clase_id, alumno_id, jornada_id, catalogo_punto_id,
            fecha, None, "Importado desde archivo", puntos,
        )
        ids_creados.append(evento_id)
    return ids_creados
