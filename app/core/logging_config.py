"""Logging estructurado a consola y archivo, con manejo centralizado de errores.

`docker logs` sigue mostrando todo por consola (stdout); además se persiste
a un archivo dentro del propio volumen de la app para consulta posterior.
"""
import logging
import logging.handlers
import os

from core.config import get_settings

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def configurar_logging() -> None:
    settings = get_settings()
    os.makedirs(LOG_DIR, exist_ok=True)

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler_consola = logging.StreamHandler()
    handler_consola.setFormatter(formato)

    handler_archivo = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler_archivo.setFormatter(formato)

    raiz = logging.getLogger()
    raiz.setLevel(settings.log_level)
    raiz.handlers = [handler_consola, handler_archivo]
