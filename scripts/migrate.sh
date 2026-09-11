#!/usr/bin/env bash
# Aplica los scripts SQL de db/migrations que todavía no se hayan aplicado,
# en orden numérico, dejando constancia en la tabla schema_migrations.
#
# Es la alternativa manual a Alembic acordada para este proyecto (sin ORM).
# Uso: ./scripts/migrate.sh   (desde la raíz del proyecto, con docker compose activo)
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
source .env
set +a

MYSQL="docker compose exec -T db mysql -u root -p${DB_ROOT_PASSWORD} ${DB_NAME}"

$MYSQL -e "
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    VARCHAR(255) PRIMARY KEY,
    applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"

for archivo in db/migrations/*.sql; do
  nombre=$(basename "$archivo")
  ya_aplicada=$($MYSQL -N -e "SELECT COUNT(*) FROM schema_migrations WHERE filename = '${nombre}';")

  if [ "$ya_aplicada" = "0" ]; then
    echo "Aplicando ${nombre}..."
    docker compose exec -T db mysql -u root -p"${DB_ROOT_PASSWORD}" "${DB_NAME}" < "$archivo"
    $MYSQL -e "INSERT INTO schema_migrations (filename) VALUES ('${nombre}');"
  else
    echo "Ya aplicada, se omite: ${nombre}"
  fi
done

echo "Esquema al día."
