#!/usr/bin/env bash
set -euo pipefail

# Export OpenAPI schema from running FastAPI app or via uvicorn on the fly.

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}
OUT=${OUT:-openapi.json}

if curl -fsS "http://$HOST:$PORT/openapi.json" >/dev/null 2>&1; then
  echo "[+] Exporting OpenAPI from running server..."
  curl -fsS "http://$HOST:$PORT/openapi.json" -o "$OUT"
  exit 0
fi

echo "[+] Launching uvicorn to export OpenAPI..."
pushd "$(dirname "$0")/.." >/dev/null
python - <<'PY'
import json
from app.api.main import create_app
app = create_app()
print(json.dumps(app.openapi()))
PY
popd >/dev/null

