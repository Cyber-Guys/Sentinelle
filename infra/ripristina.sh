#!/bin/sh
# Ripristina il dump dei dati demo se il database e' vuoto (lo lancia il servizio "dati" di compose.yaml).
# Idempotente: a database popolato non fa nulla. Il dump arriva da scripts/docker.sh (release "dati-v1").
set -eu
DUMP=/dati/sentinelle.dump

n="$(psql -tAc 'SELECT count(*) FROM incendio_storico' 2>/dev/null || true)"
if [ "${n:-0}" -gt 0 ] 2>/dev/null; then echo "dati gia' presenti ($n incendi): niente da fare"; exit 0; fi

[ -f "$DUMP" ] || { echo "Manca dati/$(basename "$DUMP"): usare ./scripts/docker.sh (scarica la release) o copiarlo a mano"; exit 1; }

echo "ripristino $DUMP"
psql -d postgres -qc 'DROP DATABASE IF EXISTS sentinelle WITH (FORCE)' -c 'CREATE DATABASE sentinelle'
pg_restore -j 4 --no-owner -d sentinelle "$DUMP" || true # avvisi innocui (es. estensione gia' presente)

n="$(psql -tAc 'SELECT count(*) FROM incendio_storico')"
[ "$n" -gt 0 ] || { echo "ripristino fallito: nessun incendio storico"; exit 1; }
echo "ok: $(psql -tAc 'SELECT count(*) FROM comune') comuni, $n incendi storici"
