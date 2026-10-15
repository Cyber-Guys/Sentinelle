#!/usr/bin/env bash
# Avvia database (se spento), backend :8000 e frontend :3000 insieme. Ctrl+C ferma tutto.
# Prima volta: ./scripts/setup.sh
set -uo pipefail
RADICE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RADICE"

echo "==> Database"
docker compose -f infra/compose.yaml up -d --wait db || {
  echo "Database non avviato: Docker e' acceso? La porta 5432 e' libera? (vedi ONBOARDING.md)"; exit 1; }

prefisso() { awk -v p="$1" '{ print p " " $0; fflush() }'; }

# Ctrl+C o uscita di uno dei due: ferma l'intero gruppo di processi (uvicorn --reload e nuxt hanno figli).
trap 'trap - INT TERM EXIT; echo; echo "==> Arresto"; kill 0 2>/dev/null' INT TERM EXIT

"$RADICE/scripts/backend.sh" 2>&1 | prefisso "[backend] " &
(cd frontend && npm run dev 2>&1) | prefisso "[frontend]" &

echo
echo "  App cittadino:      http://localhost:3000/app"
echo "  Cruscotto:          http://localhost:3000/cruscotto"
echo "  API (salute):       http://localhost:${PORTA_BACKEND:-8000}/salute"
echo "  Dal telefono:       ./scripts/tunnel.sh in un altro terminale"
echo "  Ctrl+C per fermare"
echo

wait -n 2>/dev/null || wait
