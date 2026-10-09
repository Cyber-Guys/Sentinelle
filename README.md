# Sentinelle

Segnalazione partecipata e gamification contro gli incendi in Sardegna
(GreenLab Sardegna Hackathon, challenge 2 + 3). Specifica:
`docs/specifiche/2026-10-09-sentinelle-incendi.md`. Come si lavora: `AGENTS.md`.

## Avvio

Prerequisiti: Docker Desktop, conda, Node 22.

```bash
# 1. database (PostGIS, immagine multi-arch imresamu/postgis: nativa su Apple Silicon) e dati
docker compose -f infra/compose.yaml up -d
conda create -y -n sentinelle python=3.12 && conda run -n sentinelle pip install -e "backend[dev]"
conda run -n sentinelle python scripts/scarica_dati.py   # solo la prima volta, lento (~280 MB)
conda run -n sentinelle python scripts/carica_dati.py
# tile vettoriali dello storico (frontend/public/tiles/storico.pmtiles, gia' versionato): serve solo per rigenerarli
# richiede tippecanoe (brew install tippecanoe, oppure conda-forge)
conda run -n sentinelle python scripts/genera_tiles.py

# 2. backend su :8000
cd backend && conda run --no-capture-output -n sentinelle python -m uvicorn sentinelle.main:app --app-dir src --port 8000 --reload

# 3. frontend su :3000
cd frontend && npm install && npm run dev
```

- App cittadino: http://localhost:3000/app (a larghezza telefono)
- Cruscotto operatori: http://localhost:3000/cruscotto

## Utili

- Cambiando immagine o architettura il volume va ricreato: `docker compose -f infra/compose.yaml down -v`, poi `up -d` e `carica_dati.py`.
- Prova end-to-end: `conda run -n sentinelle python scripts/prova_percorso.py`
- Test della priorita': `cd backend && conda run -n sentinelle pytest -q`
- Prova del gioco: `conda run -n sentinelle python scripts/prova_gioco.py`
- Riportare la demo a zero e seminare classifica e mappature simulate:
  `docker exec -i infra-db-1 psql -U sentinelle < scripts/reset_demo.sql && conda run -n sentinelle python scripts/semina_demo.py`
- Senza rete: `MODALITA_OFFLINE=1` per il backend (FIRMS, meteo e Corine da `dati/offline/`).
- Hook: `git config core.hooksPath .githooks`
