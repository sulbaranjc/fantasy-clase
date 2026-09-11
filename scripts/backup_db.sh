#!/usr/bin/env bash
# Genera un dump manual de la base de datos MySQL del proyecto.
# Uso: ./scripts/backup_db.sh   (desde la raíz del proyecto, con docker compose activo)
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
source .env
set +a

mkdir -p backups
ARCHIVO="backups/fantasy_clase_$(date +%Y%m%d_%H%M%S).sql.gz"

docker compose exec -T db \
  mysqldump -u root -p"${DB_ROOT_PASSWORD}" "${DB_NAME}" \
  | gzip > "${ARCHIVO}"

echo "Backup generado en: ${ARCHIVO}"
