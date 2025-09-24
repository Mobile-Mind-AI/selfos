#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is not set. Example: postgresql+psycopg://user:pass@host:5432/db" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
pushd "${SCRIPT_DIR}/.." >/dev/null

source .venv/bin/activate 2>/dev/null || true
alembic -c alembic.ini upgrade head

echo "[✓] Alembic migrations applied to ${DATABASE_URL}"
popd >/dev/null

