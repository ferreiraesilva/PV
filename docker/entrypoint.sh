#!/bin/sh
set -e

DB_DSN="${DATABASE_PLAIN_URL:-}"
APPLY_SEEDS="${APPLY_SEEDS:-false}"
SEED_FILE="${SEED_FILE:-db/seeds.sql}"

if [ -n "$DB_DSN" ]; then
  echo "[entrypoint] Waiting for database to become available..."
  until pg_isready --dbname "$DB_DSN" >/dev/null 2>&1; do
    sleep 1
  done
fi

echo "[entrypoint] Applying migrations"
alembic upgrade head

if [ "$APPLY_SEEDS" = "true" ] && [ -n "$DB_DSN" ] && [ -f "$SEED_FILE" ]; then
  echo "[entrypoint] Seeding baseline data from $SEED_FILE"
  psql "$DB_DSN" -v ON_ERROR_STOP=1 -f "$SEED_FILE"
fi

echo "[entrypoint] Starting application"
exec "$@"
