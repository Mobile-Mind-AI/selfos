#!/usr/bin/env bash
set -euo pipefail

# Local bootstrap: run Postgres with pgvector via Docker and apply Alembic migrations.

PG_IMAGE="${PG_IMAGE:-pgvector/pgvector:pg15}"
PG_CONTAINER="${PG_CONTAINER:-selfos-pg}"
PG_PORT="${PG_PORT:-5432}"
DB_USER="${DB_USER:-selfos}"
DB_PASSWORD="${DB_PASSWORD:-selfos}"
DB_NAME="${DB_NAME:-selfos_dev}"

echo "[+] Starting Postgres (${PG_IMAGE}) on localhost:${PG_PORT} (container: ${PG_CONTAINER})"

if docker ps -a --format '{{.Names}}' | grep -qx "${PG_CONTAINER}"; then
  if ! docker ps --format '{{.Names}}' | grep -qx "${PG_CONTAINER}"; then
    docker start "${PG_CONTAINER}"
  fi
else
  docker run -d --name "${PG_CONTAINER}" \
    -e POSTGRES_USER="${DB_USER}" \
    -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
    -e POSTGRES_DB="${DB_NAME}" \
    -p "${PG_PORT}:5432" \
    -v selfos_pg_data:/var/lib/postgresql/data \
    "${PG_IMAGE}"
fi

echo "[+] Waiting for Postgres to be ready..."
until docker exec -i "${PG_CONTAINER}" pg_isready -h localhost -p 5432 >/dev/null 2>&1; do
  sleep 1
done

echo "[+] Ensuring pgvector extension exists..."
docker exec -i "${PG_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS vector;"

pushd "$(dirname "$0")/.." >/dev/null

export DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@localhost:${PG_PORT}/${DB_NAME}"
echo "[+] DATABASE_URL=${DATABASE_URL}"

if [ ! -d .venv ]; then
  echo "[+] Creating virtualenv and installing requirements..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -U pip >/dev/null
pip install -r requirements.txt

echo "[+] Running Alembic migrations..."
alembic -c alembic.ini upgrade head

echo "[✓] Local DB bootstrapped and migrated."
popd >/dev/null

