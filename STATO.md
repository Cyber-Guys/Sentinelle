# Stato del lavoro

> **Riferimento:** commit `c620c93` — 2026-10-16

## Fase

Preparazione pre-hackathon (evento 16-17 ottobre, webinar 14 ottobre). Il
prototipo copre tutto il percorso della demo ed e' stato provato su telefono
vero. Si continua a migliorare la piattaforma; il pitch e' ancora da preparare.

**Progetto:** "Sentinelle" (nome provvisorio), challenge 2+3 fuse.
Specifica `docs/specifiche/2026-10-09-sentinelle-incendi.md`, decisione
`docs/decisioni/2026-10-09-direzione-e-architettura.md`. Stack Nuxt 4 +
FastAPI + PostGIS; avvio in `README.md`.

**Cosa c'e' (piani chiusi in `docs/piani/`):**
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

**Prossimo passo:** decidere col team i prossimi miglioramenti (candidati:
modalita' scenario con hotspot simulati dichiarati, pitch con numeri CFVA).

## Chi fa cosa

Ognuno modifica solo la propria riga.

| Persona | Branch | Task corrente | Piano |
|---|---|---|---|
| Alessandro | main | miglioramento piattaforma | — |
| Nicholas | — | — | — |
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

- Cruscotto su telefono: provare su telefono vero il trascinamento del foglio
  Segnalazioni (testato solo con gesti simulati).
- Senza hotspot reali la priorita' resta media in demo: valutare la modalita'
  scenario con hotspot simulati e dichiarati.
- Profilo non tecnico nel team (criterio "gruppo di lavoro").
