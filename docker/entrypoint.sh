#!/bin/sh
set -e

if [ -n "" ]; then
  echo "[entrypoint] Waiting for database to become available..."
  until pg_isready --dbname "" >/dev/null 2>&1; do
    sleep 1
  done
fi

echo "[entrypoint] Applying migrations"
alembic upgrade head

if [ "" = "true" ] && [ -n "" ] && [ -f "db/seeds.sql" ]; then
  echo "[entrypoint] Seeding baseline data"
  psql "" -v ON_ERROR_STOP=1 -f db/seeds.sql
fi

echo "[entrypoint] Starting application"
exec "$@"