# Stato del lavoro

> **Riferimento:** commit `defe1a1` — 2026-10-17

## Fase

Preparazione pre-hackathon (evento 16-17 ottobre, webinar 14 ottobre). Il
prototipo copre tutto il percorso della demo ed e' stato provato su telefono
vero. Si continua a migliorare la piattaforma; il pitch e' ancora da preparare.

**Progetto:** "Sentinelle" (nome provvisorio), challenge 2+3 fuse.
Specifica `docs/specifiche/2026-10-09-sentinelle-incendi.md`, decisione
`docs/decisioni/2026-10-09-direzione-e-architettura.md`. Stack Nuxt 4 +
FastAPI + PostGIS; avvio in `README.md`.

**Cosa c'e' (piani chiusi in `docs/piani/`):**
- Missioni mirate dal rischio: ogni giorno 3 missioni per utente nelle celle piu' a rischio entro 15 km dal comune (`missioni_mirate.py`, tabella `missione_mirata`, `GET /missioni/mirate`, `POST /missioni/mirate/{id}/completa` entro 1 km -> mappatura `sterpaglie` con riga "Da missione mirata" nel cruscotto); card in cima alla scheda Missioni e pin Target sulla mappa
- Sopralluogo mirato: `completa` richiede `esito` (pulita|sterpaglie|rifiuti), salvato in `missione_mirata.esito` e `missione_completata.esito` (DDL idempotente); mappatura `rifiuti_strada` per rifiuti, `sterpaglie` per sterpaglie e area pulita (esito distingue); `/mappature` espone `esito`. App: tocco fuori dal cerchio chiude, GPS fuori cerchio avvisa, 404/409 chiudono con toast e ricaricano.
- Acqua per spegnere (ponte challenge 4): 33 invasi CeDoc in `dati/invasi.json` (riempimento 09-2026), tabella `invaso` caricata all'avvio, `GET /invasi`, livello "Risorse idriche" (cruscotto acceso, app spento) e invasi entro 40 km nello scenario
- Dati: perimetri CFVA 2005-2025 in PostGIS e come PMTiles statico
  (`frontend/public/tiles/storico.pmtiles`); mappa base offline Protomaps
  (`sardegna.pmtiles`); FIRMS, Open-Meteo, Corine in parallelo con cache.
- App cittadino: mappa con incendi storici (pulsante Livelli), segnalazione con
  priorita' scomposta per fattore, missioni, quiz, livelli, classifica comuni,
  scheda "Le tue segnalazioni" con pin per stato e avviso alla valutazione.
- Cruscotto: coda con schede In coda / Confermate / Falsi allarmi, scheda con
  scomposizione e azioni, livelli (incendi storici, hotspot, mappature a icona
  con cluster, storico segnalazioni), versione telefono con foglio a tre altezze.
- Simulazione di scenario (cruscotto): da popup hotspot, scheda o clic destro /
  pressione lunga; aree ora per ora fino a 24 h con meteo orario, cursore e
  play, comuni raggiunti, acqua vicina, nota di onesta'. Livello "Rischio di
  oggi" a celle 2 km in app e cruscotto (piano `2026-10-16-simulazione-scenario`).
- Live: trigger Postgres -> NOTIFY -> SSE `/eventi` -> `useEventi()`; polling
  di riserva 30 s (`docs/esperimenti/2026-10-10-eventi-live.md`).
- Accesso da telefono in HTTPS: `scripts/tunnel.sh` (proxy `/api`).
- Linguaggio visivo in `docs/interfaccia/linguaggio-visivo.md` (scuro per
  primo, raggi concentrici, pin pulsanti, controlli Lucide).

**Onboarding del team:** clone pronto all'uso con `./scripts/setup.sh` (dati
dal dump della release GitHub `dati-v1`) e `./scripts/avvia.sh`; guida in
`ONBOARDING.md`. Provato su clone pulito (conteggi corretti, backend attivo).

**Fatto:** "Waze per gli incendi" (piano `2026-10-16-waze-per-gli-incendi`, chiuso): app = mappa condivisa (3 tipi: fuoco, fumo, area a rischio; conferma / "non c'e' piu'" entro 2 km, anti-doppione, alert di prossimita' con app aperta), affidabilita' calcolata (`affidabilita.py`, pesi in `pesi.toml`), cruscotto con tipi, livello, conteggi, filtro per tipo, stato ufficiale (`POST /segnalazioni/{id}/stato`, visto nell'app in < 1 s) e "Probabilmente spento". Provato in browser desktop e 375 px; telefono vero via tunnel non provato.

**Operativo nel cruscotto (fatto):** basi reali VVF/CFVA/AIB (`dati/basi.json`, `scripts/aggiorna_basi.py`, `GET /basi`; 19 con `coord_incerta` da verificare), flotta SIMULATA deterministica (`flotta.py`, `GET /flotta?t=`): mezzi di terra mai in mare (percorsi riportati sulla terraferma con l'unione dei comuni, cache calcolata all'avvio), aerei base -> invaso -> obiettivo. Icone canvas squircle/sagome in `useMappa.ts` (`registraMezzi`). Default del cruscotto: accesi solo aree critiche, incendi attivi e storico segnalazioni; storico con i segnaposti per tipo (colore = confermata, grigio = spenta/falso allarme) e popup con stato ufficiale, conferme, affidabilita'.

**Docker (fatto):** stack completo con `./scripts/docker.sh` (`compose.yaml`: db PostGIS alpine, servizio `dati` che ripristina `dati/sentinelle.dump` se il db e' vuoto, backend python slim non-root con dipendenze bloccate in `backend/requirements.txt`, frontend Nuxt statico servito da nginx che fa anche da proxy `/api` e SSE). `./scripts/docker.sh dev` = hot reload (`compose.dev.yaml`). RAM misurata: frontend 7 MiB, backend 105 MiB, db 303 MiB. Verificato su Linux/WSL2 amd64: cruscotto e `/app` a 375 px nel browser, `prova_percorso.py` nel container OK. Il flusso senza Docker (`infra/compose.yaml`, `setup.sh`, `avvia.sh`) resta ma non va usato insieme (stessa porta 3000).

**Prossimo passo:** pitch e prove su telefono vero; il dump `dati-v1` va ripubblicato (schema cambiato, `scripts/pubblica_dati.sh`).

## Chi fa cosa

Ognuno modifica solo la propria riga.

| Persona | Branch | Task corrente | Piano |
|---|---|---|---|
| Alessandro | main | Tutto committato (Waze, aree critiche, incendi attivi, operativo, storico ridisegnato). Prossimo: ripubblicare dump `dati-v1`, verificare coordinate basi incerte, provare su telefono vero, pitch | `docs/piani/2026-10-16-waze-per-gli-incendi.md` (chiuso) |
| Nicholas | nicholas/dashboard-cop | Dashboard COP (`/dashboard`, ex cruscotto) completa e verificata nel browser (1440 px e telefono, build Docker statico): ingresso 7 aree, bollettino CFD simulato da file, livelli, statistiche, scheda incendio e chiusura, segnalazioni da certificare (l'app le vede). Prossimo: prova del team, tema chiaro, merge su main | `docs/piani/2026-10-17-dashboard-cop.md` |
| Andrea | — | — | — |
| Nicola | — | — | — |

## Decisioni confermate

- Memoria condivisa nel repository (`AGENTS.md`, `STATO.md`, `docs/`); SDD
  snello, nessun reviewer, una verifica eseguibile per consegna.
- Lingua del codice: nomi di dominio in italiano, tecnici in inglese.
- Prova su telefono vero via tunnel riuscita (2026-10-10): mappa, tocchi, GPS,
  fotocamera, aggiornamenti live. I tocchi mancati erano solo dell'emulazione
  mobile del browser.

## Scoperto fuori da un piano

- Portatile di sviluppo bloccato due volte (WSL 7 GB di RAM, C: quasi pieno): calcoli PostGIS pesanti + nuxt dev +
  browser. Il bollettino CFD ora si precalcola su un PC capiente (README, "Bollettino CFD simulato").

- WFS regionale `https://webgis2.regione.sardegna.it/geoserver/dbu/ows`
  instabile: i dati vanno precaricati (`scripts/scarica_dati.py`).
- FIRMS funziona senza chiave (CSV Europa 24 h); a ottobre in Sardegna 0
  hotspot, verificato contro i dati grezzi NASA (pipeline corretta).
- Open-Meteo non fornisce FWI; licenza SardegnaSIRA CC BY-NC-ND da chiarire.
- `dati/*.geojson` (~280 MB) ignorati da Git; i PMTiles sono versionati
  (`sardegna.pmtiles` 54 MB: valutare Git LFS se si rigenera spesso).

## Da fare prima dell'evento

- [ ] Condividere specifica e ruoli con Nicholas, Andrea, Nicola.
- [ ] Scegliere il nome dell'app.
- [x] Decidere come condividere `dati/` col team: dump PostGIS nella release
      GitHub `dati-v1`, scaricato da `scripts/setup.sh`.
- [ ] Trovare l'URL del bollettino giornaliero di pericolo incendi (Protezione
      Civile Sardegna).
- [ ] Un membro registra la MAP_KEY gratuita NASA FIRMS (solo email).
- [ ] Partecipare al webinar con le domande di `docs/dominio/fonti-incendi.md`.
- [ ] Preparare il pitch (`docs/pitch/`).

## Aperto

- Docker non provato su Mac/arm64 (hot reload su Docker Desktop incluso), upload foto via nginx e tunnel da telefono. Immagine db alpine = collation musl: un `ORDER BY` su testo puo' differire dal flusso senza Docker. Decidere col team se ritirare `infra/compose.yaml`, `setup.sh` e `avvia.sh`.
- Trappola nota: un handler `styleimagemissing` che ridisegna tutte le immagini (remove+add) va in loop e blocca la mappa; ridisegnare solo se l'immagine manca davvero (`cruscotto.vue`).
- Simulazione area da hotspot lenta (~6 s): da ottimizzare se serve in demo.

- Cruscotto su telefono: provare su telefono vero il trascinamento del foglio
  Segnalazioni (testato solo con gesti simulati).
- Senza hotspot reali la priorita' resta media in demo: valutare la modalita'
  scenario con hotspot simulati e dichiarati.
- Profilo non tecnico nel team (criterio "gruppo di lavoro").
