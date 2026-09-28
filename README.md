<p align="center">
  <img src="app/static/img/logo.png" width="160" alt="Class Fantasy">
</p>

# Class Fantasy

Aplicación web que migra la lógica de la hoja de cálculo `Fantasy_Clase.xlsx`
(fantasy football aplicado al aula) a un sistema multiusuario. Ver el detalle
completo de reglas de negocio y stack técnico en [`especificaciones/`](especificaciones/):

- [Especificaciones Funcionales](especificaciones/Especificaciones_Funcionales_Fantasy_Clase.docx)
- [Especificaciones Técnicas](especificaciones/Especificaciones_Tecnicas_Fantasy_Clase.docx)

## Estado del proyecto

Fase actual: **andamiaje inicial** — la aplicación arranca, se conecta a MySQL,
sirve una página de inicio y expone un primer módulo de ejemplo (`alumnos`)
que sirve de plantilla para el resto de módulos de negocio (auth, clases,
catálogo de puntos, eventos, jornadas, plantillas, clasificación), que se
irán implementando de forma incremental junto con sus pruebas.

## Stack

Python 3.12 · FastAPI · Jinja2 · MySQL 8 (sin ORM, SQL directo asíncrono) ·
Bootstrap 5 · JavaScript vanilla · pytest · Docker Compose.

## Cómo levantar el entorno de desarrollo local

1. Copia el archivo de variables de entorno y ajusta lo que necesites:

   ```bash
   cp .env.example .env
   ```

2. Levanta los contenedores (app + base de datos):

   ```bash
   docker compose up --build
   ```

3. Aplica el esquema de base de datos (solo hace falta la primera vez, y cada
   vez que se añada un nuevo script en `db/migrations/`):

   ```bash
   ./scripts/migrate.sh
   ```

4. Abre <http://localhost:8000> — deberías ver la página de inicio. El estado
   de la conexión a base de datos se puede comprobar en
   <http://localhost:8000/salud>.

## Ejecutar las pruebas

Con los contenedores levantados:

```bash
docker compose exec app pytest
```

Las pruebas unitarias (`app/tests/unit/`) no requieren base de datos; las de
integración (`app/tests/integration/`) sí, y usan la misma base de datos del
entorno de desarrollo.

## Backups de la base de datos

```bash
./scripts/backup_db.sh
```

Genera un volcado comprimido en `backups/` (carpeta excluida de Git).

## Estructura del repositorio

```
especificaciones/     Documentos de requisitos funcionales y técnicos
Fantasy_Clase.xlsx     Hoja de cálculo original, punto de partida del proyecto
docker-compose.yml     Orquestación de contenedores (app + MySQL)
db/migrations/         Esquema de base de datos, versionado en scripts .sql
scripts/                Utilidades de operación (migraciones, backups)
app/
├── main.py             Punto de entrada de FastAPI
├── core/                Configuración, base de datos, seguridad, logging
├── modules/             Un paquete por entidad de negocio (rutas → servicio → repositorio)
├── templates/           Vistas Jinja2
├── static/              CSS y JavaScript
└── tests/               Pruebas unitarias e de integración (pytest)
```

## Flujo de trabajo con Git

Estrategia trunk-based simple: `main` siempre estable, cada funcionalidad en
una rama corta `feature/nombre-funcionalidad` que se fusiona con las pruebas
en verde. El despliegue en el servidor Proxmox se abordará una vez exista una
versión funcional estable en local.
