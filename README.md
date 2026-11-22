# Sentinelle

Segnalazione partecipata e gamification contro gli incendi in Sardegna
(GreenLab Sardegna Hackathon, challenge 2 + 3): i cittadini segnalano e
completano missioni di prevenzione, gli operatori ricevono le segnalazioni gia'
verificate e ordinate per priorita'.

## Avvio con Docker (consigliato)

Prerequisiti: Docker con compose, git, `gh` autenticato con accesso al repo (solo per il dump dei dati).
Niente Node, Python o conda sul sistema: tutto gira nei container, uguale per tutti.

```bash
./scripts/docker.sh                 # prima volta: scarica il dump dei dati (~140 MB), costruisce, ripristina, avvia (~2 min)
./scripts/docker.sh dev             # sviluppo: hot reload su backend e webapp
./scripts/docker.sh dev-dashboard   # sviluppo: hot reload sulla dashboard COP
./scripts/docker.sh bollettini 7    # genera i bollettini CFD simulati (vedi sotto, PC con almeno 16 GB di RAM)
./scripts/docker.sh down            # ferma (i dati restano); "down -v" riparte da zero
```

Tre servizi separati che parlano solo col backend (stesso database: una segnalazione fatta nell'app compare
subito nella dashboard COP):

| Servizio | Cartella | Indirizzo |
|---|---|---|
| App cittadino (`webapp`) | `webapp/` | http://localhost:3000 |
| Dashboard COP operatori (`dashboard`) | `frontend/` | http://localhost:3001/dashboard |
| Backend (`backend`) | `backend/` | http://localhost:8000/salute |

Stack leggero: webapp e dashboard statiche + nginx (~7 MB di RAM ciascuna), backend (~100 MB), PostGIS
(~300 MB). Porte: `SENTINELLE_PORTA_APP`, `SENTINELLE_PORTA_DASHBOARD`, `SENTINELLE_PORTA_API`. Senza `gh`:
copiare `sentinelle.dump` in `dati/` e lanciare lo script. Comandi nel backend:
`./scripts/docker.sh exec -T backend python scripts/prova_webapp.py`. Dipendenze Python bloccate in
`backend/requirements.txt` (comando di rigenerazione in `backend/Dockerfile`).

App cittadino senza GPS (computer, prove): aggiungere `?pos=39.4216,8.9223&dir=45` all'indirizzo per fissare
posizione e direzione dello sguardo. Dal telefono usa l'indirizzo HTTPS del tunnel che lo script stampa a fine
avvio (vedi "Prova da telefono").

## Mappa base della dashboard COP

Predefinita la **satellitare** (immagini Esri World Imagery, **serve la rete**); in alternativa la **stradale**
vettoriale, tutta offline. Si cambia dalla barra in alto e la scelta resta nel browser. Se le immagini non
arrivano (rete della sala giu') la dashboard passa da sola alla stradale e lo dice.

## Bollettino CFD simulato (dashboard COP)

Le zone di rischio della dashboard vengono da un bollettino del Centro Funzionale Decentrato **simulato**
(verde, arancione, rosso, emesso il giorno prima). Calcolarlo costa ~10 s e molta RAM per ogni giorno: su un
portatile con poca memoria blocca il PC. Per questo il backend non lo calcola mai, legge i file JSON in
`dati/bollettini/`. Si generano una volta su un PC capiente e si committano.

Chi genera (PC con almeno 16 GB di RAM):

```bash
git pull                              # branch con la dashboard COP
./scripts/docker.sh                   # stack acceso e ricostruito col codice aggiornato
./scripts/docker.sh bollettini 7      # 7 giorni da oggi; per partire da un'altra data: bollettini 7 2026-10-20
git add dati/bollettini && git commit -m "bollettini CFD simulati" && git push
```

Il comando gira nel container backend e scrive in `dati/bollettini/` un file per giorno
(`bollettino-AAAA-MM-GG.json`, ~350 KB) piu' `aree-cop.json` con i confini delle 7 aree. Richiede ~15 s per
giorno. Senza Docker, con l'ambiente di `setup.sh`: `./scripts/python.sh scripts/genera_bollettino.py --giorni 7`.

Chi usa i file (anche il PC della demo): `git pull`, poi `./scripts/docker.sh` (i file entrano nell'immagine del
backend alla build). Se manca il giorno richiesto il backend usa il file del giorno piu' vicino; se non c'e'
nessun file la mappa resta senza zone (tutto verde). Per la demo generare i giorni dell'evento.

## Avvio rapido senza Docker per l'app (ambiente sul sistema)

Prerequisiti: Docker (acceso), Node >= 20, git, e uno tra conda, uv o Python 3.12.
Per i dati serve `gh` autenticato con accesso al repo. Dettagli in `ONBOARDING.md`.

```bash
git clone https://github.com/Cyber-Guys/Sentinelle.git
cd Sentinelle
./scripts/setup.sh     # una volta: ambiente, dipendenze, database, dati demo (idempotente)
./scripts/avvia.sh     # ogni volta: backend + frontend, Ctrl+C ferma entrambi
```

- App cittadino (vecchia): http://localhost:3000/app (pensata per il telefono)
- Dashboard COP: http://localhost:3000/dashboard (`/cruscotto` reindirizza qui)
- API: http://localhost:8000/salute

Il browser chiama sempre `/api/**`: Nuxt lo inoltra al backend su :8000.
In Claude Code gli stessi server partono da `.claude/launch.json`.

## Prova da telefono

GPS e fotocamera richiedono HTTPS. Con Docker il tunnel parte da solo: `./scripts/docker.sh` crea un
Cloudflare Quick Tunnel verso la sola app cittadino e a fine avvio stampa l'indirizzo
`https://xxxx.trycloudflare.com` e un QR code da inquadrare. L'indirizzo cambia a ogni avvio; per
ristamparlo: `./scripts/docker.sh tunnel`. Chiunque lo conosca vede l'app finche' lo stack e' acceso;
cruscotto e backend restano fuori, e dal tunnel passano solo le rotte dell'app cittadino (le azioni degli
operatori rispondono 403). Senza tunnel: `SENTINELLE_TUNNEL=0 ./scripts/docker.sh`.

Senza Docker (flusso sul sistema): `./scripts/tunnel.sh` in un altro terminale (richiede `cloudflared` e
`qrencode`), che punta a localhost:3000.

## Comandi utili

`./scripts/python.sh` esegue il Python dell'ambiente creato da setup (conda o venv).

| Cosa | Comando |
|---|---|
| Riportare la demo a zero e riseminare la classifica | `docker compose -f infra/compose.yaml exec -T db psql -U sentinelle < scripts/reset_demo.sql && ./scripts/python.sh scripts/semina_demo.py` |
| Test della priorita' | `cd backend && ../scripts/python.sh -m pytest -q` |
| Prova end-to-end (backend attivo) | `./scripts/python.sh scripts/prova_percorso.py` |
| Prova del backend della webapp cittadino (utenti, localita', avvisi, media, storico) | `./scripts/docker.sh exec -T backend python scripts/prova_webapp.py` |
| Prova del gioco (backend attivo) | `./scripts/python.sh scripts/prova_gioco.py` |
| Senza rete (FIRMS, meteo, Corine da `dati/offline/`) | `MODALITA_OFFLINE=1 ./scripts/avvia.sh` |
| Rigenerare i tile dello storico (richiede tippecanoe) | `./scripts/python.sh scripts/genera_tiles.py` |
| Ricaricare i dati dalla Regione (lento, ~280 MB) | `./scripts/python.sh scripts/scarica_dati.py && ./scripts/python.sh scripts/carica_dati.py` |
| Aggiornare i volumi degli invasi (CeDoc, mensile) | `./scripts/python.sh scripts/aggiorna_invasi.py` (riscrive `dati/invasi.json`, il backend lo ricarica all'avvio) |
| Aggiornare le basi operative (VVF, CFVA, basi elicotteri AIB) | `./scripts/python.sh scripts/aggiorna_basi.py` (Overpass + Nominatim, riscrive `dati/basi.json`, il backend lo ricarica all'avvio) |
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
