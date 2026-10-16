# Sentinelle

Segnalazione partecipata e gamification contro gli incendi in Sardegna
(GreenLab Sardegna Hackathon, challenge 2 + 3): i cittadini segnalano e
completano missioni di prevenzione, gli operatori ricevono le segnalazioni gia'
verificate e ordinate per priorita'.

## Avvio rapido

Prerequisiti: Docker (acceso), Node >= 20, git, e uno tra conda, uv o Python 3.12.
Per i dati serve `gh` autenticato con accesso al repo. Dettagli in `ONBOARDING.md`.

```bash
git clone https://github.com/ale24cocco/hackaton-incendi.git
cd hackaton-incendi
./scripts/setup.sh     # una volta: ambiente, dipendenze, database, dati demo (idempotente)
./scripts/avvia.sh     # ogni volta: backend + frontend, Ctrl+C ferma entrambi
```

- App cittadino: http://localhost:3000/app (pensata per il telefono)
- Cruscotto operatori: http://localhost:3000/cruscotto
- API: http://localhost:8000/salute

Il browser chiama sempre `/api/**`: Nuxt lo inoltra al backend su :8000.
In Claude Code gli stessi server partono da `.claude/launch.json`.

## Prova da telefono

GPS e fotocamera richiedono HTTPS. Con l'app avviata, in un altro terminale:

```bash
./scripts/tunnel.sh    # richiede cloudflared e qrencode (brew install cloudflared qrencode)
```

Stampa l'URL pubblico di `/app` e un QR code da inquadrare. Ctrl+C chiude il tunnel.

## Comandi utili

`./scripts/python.sh` esegue il Python dell'ambiente creato da setup (conda o venv).

| Cosa | Comando |
|---|---|
| Riportare la demo a zero e riseminare la classifica | `docker compose -f infra/compose.yaml exec -T db psql -U sentinelle < scripts/reset_demo.sql && ./scripts/python.sh scripts/semina_demo.py` |
| Test della priorita' | `cd backend && ../scripts/python.sh -m pytest -q` |
| Prova end-to-end (backend attivo) | `./scripts/python.sh scripts/prova_percorso.py` |
| Prova del gioco (backend attivo) | `./scripts/python.sh scripts/prova_gioco.py` |
| Senza rete (FIRMS, meteo, Corine da `dati/offline/`) | `MODALITA_OFFLINE=1 ./scripts/avvia.sh` |
| Rigenerare i tile dello storico (richiede tippecanoe) | `./scripts/python.sh scripts/genera_tiles.py` |
| Ricaricare i dati dalla Regione (lento, ~280 MB) | `./scripts/python.sh scripts/scarica_dati.py && ./scripts/python.sh scripts/carica_dati.py` |
| Precalcolare le celle del Rischio di oggi (tabella `cella`; una tantum, ~11 min la prima volta, lo fa `setup.sh` se la tabella e' vuota) | `./scripts/python.sh scripts/prepara_celle.py` |
| Pubblicare un nuovo dump dei dati per il team | `./scripts/pubblica_dati.sh` |
| Ricreare il database da zero | `docker compose -f infra/compose.yaml down -v && ./scripts/setup.sh` |

Mappa base Protomaps offline in `frontend/public/tiles/sardegna.pmtiles` (OSM,
zoom 0-14). Per rigenerarla (`brew install pmtiles`, build recente da
https://maps.protomaps.com/builds/):
`pmtiles extract https://build.protomaps.com/20261009.pmtiles frontend/public/tiles/sardegna.pmtiles --bbox=7.9,38.75,10.0,41.35 --maxzoom=14`

## Struttura

```text
backend/    FastAPI + PostGIS: verifica e priorita' delle segnalazioni, gioco, eventi live (SSE)
frontend/   Nuxt 4: app cittadino e cruscotto operatori, mappe offline (PMTiles)
infra/      docker compose del database e schema
scripts/    setup, avvio, dati, prove, tunnel
docs/       memoria del progetto: specifiche, decisioni, piani, dominio, pitch
```

Come si lavora (persone e agenti): `AGENTS.md`. Dove siamo: `STATO.md`.
Per chi arriva ora: `ONBOARDING.md`.
