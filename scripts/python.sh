#!/usr/bin/env bash
# Esegue il Python dell'ambiente creato da scripts/setup.sh, qualunque esso sia:
# backend/.venv (uv o venv) se esiste, altrimenti l'ambiente conda "sentinelle".
# Uso: ./scripts/python.sh scripts/prova_percorso.py   |   ./scripts/python.sh -m pytest -q
set -euo pipefail
RADICE="$(cd "$(dirname "$0")/.." && pwd)"

if [ -x "$RADICE/backend/.venv/bin/python" ]; then
  exec "$RADICE/backend/.venv/bin/python" "$@"
fi
if command -v conda >/dev/null 2>&1; then
  PY="$(conda info --base 2>/dev/null)/envs/sentinelle/bin/python"
  [ -x "$PY" ] && exec "$PY" "$@"
fi
echo "Ambiente Python di Sentinelle non trovato: eseguire ./scripts/setup.sh" >&2
exit 1
