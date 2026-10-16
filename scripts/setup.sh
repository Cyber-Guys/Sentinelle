#!/usr/bin/env bash
# Prepara un clone appena scaricato: prerequisiti, hook, ambiente Python, npm, database e dati demo.
# Idempotente: si puo' rilanciare quando si vuole, salta cio' che e' gia' pronto.
#
# Uso (dalla radice del repo):
#   ./scripts/setup.sh                    dati dalla release GitHub "dati-v1" (richiede gh autenticato)
#   ./scripts/setup.sh --dump file.dump   dati da un dump locale (pg_dump -Fc)
#
# Variabili opzionali:
#   SENTINELLE_PORTA_DB=5433   porta del database se la 5432 e' occupata (scrive DATABASE_URL in .env)
#   SENTINELLE_PYTHON=conda|uv|venv   forza il tipo di ambiente Python (default: il primo disponibile)
set -euo pipefail
RADICE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RADICE"

REPO_DATI="ale24cocco/hackaton-incendi"
RELEASE_DATI="dati-v1"
FILE_DUMP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dump) FILE_DUMP="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; shift 2 ;;
    *) echo "Opzione sconosciuta: $1"; exit 2 ;;
  esac
done

passo() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
ok() { printf '    \033[32mok\033[0m %s\n' "$*"; }
manca() { printf '    \033[31mmanca\033[0m %s\n' "$*"; MANCANTI=1; }
COMPOSE=(docker compose -f infra/compose.yaml)
PSQL=("${COMPOSE[@]}" exec -T db psql -U sentinelle -d sentinelle -v ON_ERROR_STOP=1)

# --- 1. prerequisiti -------------------------------------------------------------------------------
passo "1/7 Prerequisiti"
MANCANTI=0
command -v git >/dev/null && ok "git" || manca "git  -> macOS: xcode-select --install | Linux: sudo apt install git"
if command -v docker >/dev/null; then
  if docker info >/dev/null 2>&1; then ok "docker (attivo)"
  else manca "docker installato ma spento -> avviare Docker Desktop (macOS) o: sudo systemctl start docker"; fi
else manca "docker -> https://docs.docker.com/get-docker/ (macOS: Docker Desktop)"; fi
if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 20 ]; then ok "node $(node -v)"
else manca "node >= 20 -> https://nodejs.org (o: brew install node@22 | nvm install 22)"; fi

TIPO_PY="${SENTINELLE_PYTHON:-}"
if [ -z "$TIPO_PY" ]; then
  if command -v conda >/dev/null; then TIPO_PY=conda
  elif command -v uv >/dev/null; then TIPO_PY=uv
  else TIPO_PY=venv; fi
fi
case "$TIPO_PY" in
  conda) command -v conda >/dev/null && ok "conda (ambiente 'sentinelle')" || manca "conda" ;;
  uv) command -v uv >/dev/null && ok "uv (backend/.venv, Python 3.12)" || manca "uv -> curl -LsSf https://astral.sh/uv/install.sh | sh" ;;
  venv) command -v python3.12 >/dev/null && ok "python3.12 (backend/.venv)" \
    || manca "Python 3.12 -> consigliato uv: curl -LsSf https://astral.sh/uv/install.sh | sh (oppure brew install python@3.12 | sudo apt install python3.12-venv)" ;;
esac
[ "$MANCANTI" -eq 0 ] || { echo; echo "Installare quanto manca e rilanciare ./scripts/setup.sh"; exit 1; }

# --- 2. hook git e .env ----------------------------------------------------------------------------
passo "2/7 Hook git e .env"
git config core.hooksPath .githooks && ok "core.hooksPath = .githooks (avviso pre-commit su STATO.md)"
PORTA_DB="${SENTINELLE_PORTA_DB:-5432}"
export SENTINELLE_PORTA_DB="$PORTA_DB"
export DATABASE_URL="postgresql+psycopg://sentinelle:sentinelle@localhost:$PORTA_DB/sentinelle"
if [ ! -f .env ]; then
  echo "DATABASE_URL=$DATABASE_URL" > .env && ok ".env creato (porta DB $PORTA_DB)"
elif [ "$PORTA_DB" != 5432 ] && ! grep -q "localhost:$PORTA_DB/" .env; then
  echo "    attenzione: .env esiste ma non usa la porta $PORTA_DB: aggiornare DATABASE_URL a mano"
else ok ".env presente"; fi

# --- 3. ambiente Python ----------------------------------------------------------------------------
passo "3/7 Ambiente Python ($TIPO_PY)"
case "$TIPO_PY" in
  conda)
    if [ ! -x "$(conda info --base)/envs/sentinelle/bin/python" ]; then
      conda create -y -q -n sentinelle python=3.12 >/dev/null
    fi
    "$(conda info --base)/envs/sentinelle/bin/python" -m pip install -q -e "backend[dev]" ;;
  uv)
    [ -x backend/.venv/bin/python ] || uv venv -q --python 3.12 backend/.venv
    uv pip install -q --python backend/.venv/bin/python -e "backend[dev]" ;;
  venv)
    [ -x backend/.venv/bin/python ] || python3.12 -m venv backend/.venv
    backend/.venv/bin/python -m pip install -q -e "backend[dev]" ;;
esac
ok "backend[dev] installato: $(./scripts/python.sh -c 'import sys; print(sys.executable)')"

# --- 4. frontend -----------------------------------------------------------------------------------
passo "4/7 Dipendenze frontend (npm ci)"
(cd frontend && npm ci --no-audit --no-fund --loglevel=error >/dev/null) && ok "frontend/node_modules"

# --- 5. database -----------------------------------------------------------------------------------
passo "5/7 Database PostGIS (porta $PORTA_DB)"
"${COMPOSE[@]}" up -d --wait db || {
  echo "Avvio fallito. Porta $PORTA_DB occupata? Riprovare con SENTINELLE_PORTA_DB=5433 ./scripts/setup.sh"; exit 1; }
ok "database pronto"

# --- 6. dati ---------------------------------------------------------------------------------------
passo "6/7 Dati"
conta() { "${PSQL[@]}" -tAc "$1" 2>/dev/null | tr -d '[:space:]' || true; }
ripristina() {  # $1 = file .dump: ricrea il database e lo ripristina
  "${COMPOSE[@]}" exec -T db sh -c 'dropdb -U sentinelle --if-exists --force sentinelle && createdb -U sentinelle sentinelle'
  "${COMPOSE[@]}" exec -T db pg_restore -U sentinelle -d sentinelle --no-owner < "$1" || true
}
if [ "$(conta 'SELECT count(*) FROM incendio_storico')" -gt 0 ] 2>/dev/null; then
  ok "database gia' popolato: salto il caricamento"
elif [ -n "$FILE_DUMP" ]; then
  echo "    ripristino da $FILE_DUMP"; ripristina "$FILE_DUMP"; ok "dump ripristinato"
elif command -v gh >/dev/null && gh auth status >/dev/null 2>&1 \
     && TMP="$(mktemp -d)" && gh release download "$RELEASE_DATI" --repo "$REPO_DATI" -p 'sentinelle.dump' -D "$TMP"; then
  echo "    scaricato $RELEASE_DATI da $REPO_DATI ($(du -h "$TMP/sentinelle.dump" | cut -f1))"
  ripristina "$TMP/sentinelle.dump"; rm -rf "$TMP"; ok "dump ripristinato"
elif ls dati/comuni.geojson >/dev/null 2>&1; then
  echo "    release non disponibile: carico i GeoJSON di dati/"
  ./scripts/python.sh scripts/carica_dati.py && ok "GeoJSON caricati"
else
  echo "    Nessuna fonte di dati disponibile. Una delle tre:"
  echo "      - gh auth login (serve accesso al repo $REPO_DATI) e rilanciare ./scripts/setup.sh"
  echo "      - chiedere il file sentinelle.dump e lanciare ./scripts/setup.sh --dump sentinelle.dump"
  echo "      - scaricare dalla Regione (lento, ~280 MB, WFS instabile):"
  echo "        ./scripts/python.sh scripts/scarica_dati.py && ./scripts/setup.sh"
  exit 1
fi
./scripts/python.sh scripts/semina_demo.py >/dev/null && ok "classifica demo seminata (utenti '(demo)')"
if [ "$(conta 'SELECT count(*) FROM cella')" -gt 0 ] 2>/dev/null; then
  ok "celle del rischio gia' calcolate"
else
  ./scripts/python.sh scripts/prepara_celle.py && ok "celle del rischio calcolate"
fi

# --- 7. verifica -----------------------------------------------------------------------------------
passo "7/7 Verifica"
COMUNI="$(conta 'SELECT count(*) FROM comune')"
INCENDI="$(conta 'SELECT count(*) FROM incendio_storico')"
echo "    comuni: $COMUNI (attesi 377)   incendi storici: $INCENDI (attesi 27544)"
(cd backend && ../scripts/python.sh -m pytest -q 2>&1 | tail -1 | sed 's/^/    pytest: /')
if [ "$COMUNI" = 377 ] && [ "$INCENDI" = 27544 ]; then
  printf '\n\033[32mPronto.\033[0m Avvio: ./scripts/avvia.sh  (poi http://localhost:3000/app)\n'
else
  printf '\n\033[33mConteggi diversi dal previsto\033[0m: dati incompleti, vedi ONBOARDING.md "Problemi frequenti".\n'
  exit 1
fi
