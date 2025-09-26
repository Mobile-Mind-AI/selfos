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

echo "[+] Generating OpenAPI without server..."
pushd "$(dirname "$0")/.." >/dev/null
PYBIN="python3"
if [ -x .venv/bin/python ]; then PYBIN=".venv/bin/python"; fi
"$PYBIN" - <<'PY' > "$OUT"
import json
from app.api.main import create_app
app = create_app()
print(json.dumps(app.openapi()))
PY
echo "[✓] OpenAPI written to $OUT"
popd >/dev/null
