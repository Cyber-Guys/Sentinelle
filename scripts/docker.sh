#!/usr/bin/env bash
# Avvia lo stack Docker: db, backend, webapp (cittadino), dashboard (operatori) e il tunnel HTTPS per il telefono.
# Al primo avvio scarica il dump dei dati demo (release GitHub "dati-v1", serve gh autenticato) in
# dati/sentinelle.dump e lo ripristina.
# Uso:  ./scripts/docker.sh                stack leggero (webapp e dashboard statiche + nginx) + tunnel
#       ./scripts/docker.sh dev            hot reload su backend e webapp (compose.dev.yaml)
#       ./scripts/docker.sh dev-dashboard  hot reload sul cruscotto (compose.dev-dashboard.yaml)
#       ./scripts/docker.sh tunnel         ristampa indirizzo e QR code del tunnel gia' acceso
#       ./scripts/docker.sh down           ferma (i dati restano); "down -v" li cancella
# Qualunque altro argomento va a docker compose (es. logs -f backend, ps, exec -T backend python scripts/...).
# SENTINELLE_TUNNEL=0 avvia senza tunnel (l'app resta solo su localhost).
set -euo pipefail
cd "$(dirname "$0")/.."

FILE_DUMP=dati/sentinelle.dump
FILE=(--profile tunnel -f compose.yaml)  # il profilo serve anche a down/logs/ps, che altrimenti ignorano il tunnel
CMD=("$@")
case "${1:-}" in
  dev) FILE+=(-f compose.dev.yaml); CMD=() ;;
  dev-dashboard) FILE+=(-f compose.dev-dashboard.yaml); CMD=() ;;
  tunnel) CMD=(tunnel) ;;
esac

# Indirizzo https://xxxx.trycloudflare.com dai log di cloudflared (casuale, cambia a ogni avvio del servizio).
# Aspetta che risponda davvero: il nome impiega qualche secondo a diventare raggiungibile.
mostra_tunnel() {
  local url="" i
  for i in $(seq 1 60); do
    url="$(docker compose "${FILE[@]}" logs tunnel 2>/dev/null | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1 || true)"
    [ -n "$url" ] && break
    sleep 1
  done
  if [ -z "$url" ]; then echo "  Tunnel: indirizzo non trovato, vedere: ./scripts/docker.sh logs tunnel"; return 0; fi
  if command -v curl >/dev/null; then
    for i in $(seq 1 40); do curl -fsS -o /dev/null -m 4 "$url/api/salute" 2>/dev/null && break; sleep 1; done
  fi
  echo
  echo "  Dal telefono (HTTPS: GPS e fotocamera funzionano):"
  echo "    $url"
  echo
  if command -v qrencode >/dev/null; then qrencode -t ansiutf8 "$url"
  else docker run --rm node:22-alpine sh -c 'cd /tmp && npm i --silent --no-audit --no-fund qrcode-terminal >/dev/null 2>&1 \
    && node -e "require(\"qrcode-terminal\").generate(process.argv[1],{small:true})" "$1"' sh "$url" 2>/dev/null || true; fi
  echo "  Chiunque abbia questo indirizzo vede l'app finche' lo stack e' acceso. Si ferma con: ./scripts/docker.sh down"
}

if [ "${CMD[0]:-}" = tunnel ]; then
  mostra_tunnel
elif [ ${#CMD[@]} -eq 0 ]; then
  if [ ! -f "$FILE_DUMP" ] && ! docker compose "${FILE[@]}" ps -aq db 2>/dev/null | grep -q .; then
    echo "==> Scarico il dump dei dati (una volta, ~140 MB)"
    gh release download dati-v1 --repo ale24cocco/hackaton-incendi -p sentinelle.dump -D dati || {
      echo "Dump non scaricato: gh auth login (serve accesso al repo) oppure copiare il file in $FILE_DUMP"; exit 1; }
  fi
  SERVIZI=()
  if [ "${SENTINELLE_TUNNEL:-1}" = 0 ]; then
    docker compose "${FILE[@]}" stop tunnel >/dev/null 2>&1 || true
    SERVIZI=(db dati backend webapp dashboard)
  fi
  docker compose "${FILE[@]}" up -d --build --remove-orphans --wait "${SERVIZI[@]}"
  echo
  echo "  App cittadino:   http://localhost:${SENTINELLE_PORTA_APP:-3000}"
  echo "  Cruscotto:       http://localhost:${SENTINELLE_PORTA_DASHBOARD:-3001}/cruscotto"
  echo "  API (salute):    http://localhost:${SENTINELLE_PORTA_API:-8000}/salute"
  echo "  Prove senza GPS: aggiungere ?pos=39.4216,8.9223&dir=45 all'indirizzo dell'app"
  echo "  Log: ./scripts/docker.sh logs -f   Ferma: ./scripts/docker.sh down"
  [ "${SENTINELLE_TUNNEL:-1}" = 0 ] || mostra_tunnel
else
  exec docker compose "${FILE[@]}" "${CMD[@]}"
fi
