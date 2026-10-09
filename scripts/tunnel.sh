#!/usr/bin/env bash
# Tunnel HTTPS pubblico (Cloudflare Quick Tunnel) verso il frontend :3000, per provare l'app dal telefono
# (GPS e fotocamera richiedono HTTPS). Stampa l'URL di /app e un QR code. Ctrl+C per chiudere.
# Richiede: brew install cloudflared qrencode  (frontend e backend gia' attivi)
set -euo pipefail

LOG="$(mktemp)"
cloudflared tunnel --url http://localhost:3000 --no-autoupdate >"$LOG" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null; rm -f "$LOG"' EXIT INT TERM

URL=""
for _ in $(seq 1 60); do
  URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" | head -1 || true)"
  [ -n "$URL" ] && break
  kill -0 "$PID" 2>/dev/null || { cat "$LOG"; exit 1; }
  sleep 1
done
[ -n "$URL" ] || { echo "URL del tunnel non trovato"; cat "$LOG"; exit 1; }

echo
echo "Sentinelle da telefono: $URL/app"
echo "Cruscotto:              $URL/cruscotto"
echo
qrencode -t ansiutf8 "$URL/app"
echo
echo "Ctrl+C per chiudere il tunnel."
wait "$PID"
