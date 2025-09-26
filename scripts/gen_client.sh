#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
CLIENT_DIR="$ROOT_DIR/packages/shared/client"

mkdir -p "$CLIENT_DIR"

pushd "$API_DIR" >/dev/null
OUT=openapi.json ./scripts/export_openapi.sh > "$CLIENT_DIR/.openapi.log" 2>&1 || true
popd >/dev/null

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to generate the TypeScript client (install Node.js)" >&2
  exit 1
fi

npx --yes openapi-typescript "$API_DIR/openapi.json" -o "$CLIENT_DIR/index.ts"
echo "[✓] Generated TypeScript client at packages/shared/client/index.ts"

