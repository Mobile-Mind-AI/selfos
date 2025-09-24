#!/usr/bin/env bash
set -euo pipefail

# Apply Alembic migrations to a Cloud SQL Postgres instance using Cloud SQL Proxy.

if ! command -v cloud-sql-proxy >/dev/null 2>&1; then
  echo "cloud-sql-proxy is required. Install: https://cloud.google.com/sql/docs/postgres/sql-proxy" >&2
  exit 1
fi
if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI is required. Install: https://cloud.google.com/sdk" >&2
  exit 1
fi

INSTANCE="${CLOUDSQL_INSTANCE:?Set CLOUDSQL_INSTANCE, e.g. my-proj:us-central1:selfos-dev}"
DB_NAME="${DB_NAME:-selfos_dev}"
DB_USER="${DB_USER:-selfos}"
DB_PASSWORD="${DB_PASSWORD:-selfos}"
SUPERUSER="${DB_SUPERUSER:-postgres}"
SUPERPASS="${DB_SUPERPASS:-}"
LOCAL_PORT="${LOCAL_PORT:-6543}"

echo "[+] Starting Cloud SQL Proxy on localhost:${LOCAL_PORT} for ${INSTANCE}..."
cloud-sql-proxy --port "${LOCAL_PORT}" "${INSTANCE}" >/dev/null 2>&1 &
PROXY_PID=$!
trap 'kill ${PROXY_PID} >/dev/null 2>&1 || true' EXIT

echo "[+] Waiting for proxy to accept connections..."
until nc -z 127.0.0.1 "${LOCAL_PORT}" >/dev/null 2>&1; do sleep 1; done

echo "[+] Ensuring pgvector extension exists on Cloud SQL..."
if [ -n "${SUPERPASS}" ]; then export PGPASSWORD="${SUPERPASS}"; fi
psql "host=127.0.0.1 port=${LOCAL_PORT} dbname=${DB_NAME} user=${SUPERUSER}" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS vector;"

export DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${LOCAL_PORT}/${DB_NAME}"
echo "[+] DATABASE_URL=${DATABASE_URL}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
pushd "${SCRIPT_DIR}/.." >/dev/null

source .venv/bin/activate 2>/dev/null || true
pip install -r requirements.txt >/dev/null
alembic -c alembic.ini upgrade head

echo "[✓] Cloud SQL migrated successfully."
popd >/dev/null

