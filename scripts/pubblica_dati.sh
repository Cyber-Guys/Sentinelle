#!/usr/bin/env bash
# Rigenera il dump dei dati demo e lo pubblica come asset della release GitHub "dati-v1",
# da cui scripts/setup.sh lo scarica nei nuovi clone. Da lanciare solo quando cambiano i dati.
# Riporta prima la demo a zero (reset_demo.sql + semina_demo.py) per non pubblicare segnalazioni di prova.
set -euo pipefail
RADICE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RADICE"
TAG="dati-v1"
DUMP="$(mktemp -d)/sentinelle.dump"

docker compose -f infra/compose.yaml exec -T db psql -U sentinelle -q < scripts/reset_demo.sql
./scripts/python.sh scripts/semina_demo.py >/dev/null
docker compose -f infra/compose.yaml exec -T db pg_dump -U sentinelle -Fc --no-owner sentinelle > "$DUMP"
echo "Dump: $DUMP ($(du -h "$DUMP" | cut -f1))"

if gh release view "$TAG" >/dev/null 2>&1; then
  gh release upload "$TAG" "$DUMP" --clobber
else
  gh release create "$TAG" "$DUMP" --title "Dati demo" \
    --notes "Dump PostGIS (pg_dump -Fc) con comuni, perimetri CFVA 2005-2025, pericolo AIB e classifica demo simulata. Lo usa scripts/setup.sh."
fi
