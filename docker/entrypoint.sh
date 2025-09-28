#!/bin/sh
set -e

if [ -n "$DATABASE_PLAIN_URL" ]; then
  echo "[entrypoint] Waiting for database to become available..."
  until pg_isready --dbname "$DATABASE_PLAIN_URL" >/dev/null 2>&1; do
    sleep 1
  done
fi

echo "[entrypoint] Applying migrations"
alembic upgrade head

if [ "${APPLY_SEEDS:-true}" = "true" ] && [ -n "$DATABASE_PLAIN_URL" ] && [ -f "db/seeds.sql" ]; then
  echo "[entrypoint] Seeding baseline data"
  psql "$DATABASE_PLAIN_URL" -v ON_ERROR_STOP=1 -f db/seeds.sql
fi

echo "[entrypoint] Starting application"
exec "$@"
