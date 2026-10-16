#!/usr/bin/env bash
# Avvia lo stack Docker (db, backend, frontend). Al primo avvio scarica il dump dei dati demo
# (release GitHub "dati-v1", serve gh autenticato) in dati/sentinelle.dump e lo ripristina.
# Uso:  ./scripts/docker.sh         stack leggero (frontend statico + nginx)
#       ./scripts/docker.sh dev     hot reload su backend e frontend (compose.dev.yaml)
#       ./scripts/docker.sh down    ferma (i dati restano); "down -v" li cancella
# Qualunque altro argomento va a docker compose (es. logs -f backend, ps).
set -euo pipefail
cd "$(dirname "$0")/.."

FILE_DUMP=dati/sentinelle.dump
FILE=(-f compose.yaml)
CMD=("$@")
if [ "${1:-}" = dev ]; then FILE+=(-f compose.dev.yaml); CMD=(); fi

if [ ${#CMD[@]} -eq 0 ]; then
  if [ ! -f "$FILE_DUMP" ] && ! docker compose "${FILE[@]}" ps -aq db 2>/dev/null | grep -q .; then
    echo "==> Scarico il dump dei dati (una volta, ~140 MB)"
    gh release download dati-v1 --repo ale24cocco/hackaton-incendi -p sentinelle.dump -D dati || {
      echo "Dump non scaricato: gh auth login (serve accesso al repo) oppure copiare il file in $FILE_DUMP"; exit 1; }
  fi
  docker compose "${FILE[@]}" up -d --build --wait
  echo
  echo "  App cittadino:  http://localhost:${SENTINELLE_PORTA_APP:-3000}/app"
  echo "  Cruscotto:      http://localhost:${SENTINELLE_PORTA_APP:-3000}/cruscotto"
  echo "  API (salute):   http://localhost:${SENTINELLE_PORTA_API:-8000}/salute"
  echo "  Log: ./scripts/docker.sh logs -f   Ferma: ./scripts/docker.sh down"
else
  exec docker compose "${FILE[@]}" "${CMD[@]}"
fi
