"""Instancia única de Jinja2Templates, compartida por todos los módulos."""
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
