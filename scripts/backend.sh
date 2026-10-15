#!/usr/bin/env bash
# Avvia il backend FastAPI con reload (usato da scripts/avvia.sh e da .claude/launch.json).
# Porta: PORTA_BACKEND (default 8000; il frontend inoltra /api a :8000).
set -euo pipefail
RADICE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RADICE/backend"
exec "$RADICE/scripts/python.sh" -m uvicorn sentinelle.main:app --app-dir src \
  --port "${PORTA_BACKEND:-8000}" --reload --timeout-graceful-shutdown 2
