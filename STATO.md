# Stato del lavoro

> **Riferimento:** commit `50ccb01` — 2026-10-10

## Fase

Preparazione pre-hackathon (evento 16-17 ottobre, webinar 14 ottobre).
Materiali e criteri di valutazione sintetizzati in `docs/materiali/README.md`.
Fonti dati analizzate e verificate in `docs/dominio/fonti-*.md`.
Il cruscotto mostra anche gli incendi storici CFVA (livello in cima ai Livelli, logica condivisa con l'app in `useMappa.ts`).
Il box Segnalazioni del cruscotto ha le schede In coda / Confermate / Falsi allarmi (righe valutate, scheda in sola lettura).
Le mappature dei cittadini nel cruscotto sono segnaposto a icona discreti (vetro scuro, anello e icona nel colore del tipo) raggruppati in cluster fino a zoom 11 (`registraSegnaposti()` in `useMappa.ts`).
App e cruscotto si aggiornano in tempo reale: trigger Postgres -> NOTIFY -> `GET /eventi` (SSE) -> `useEventi()`; polling ridotto a 30 s (piano `docs/piani/2026-10-10-eventi-live.md`, misure in `docs/esperimenti/2026-10-10-eventi-live.md`).
Cruscotto su telefono (< 768 px): header a una fila, colonna destra come l'app, foglio Segnalazioni a tre altezze trascinabile con dettaglio e azioni nel piede, legenda nel pannello Livelli (`docs/interfaccia/linguaggio-visivo.md`, "Cruscotto su telefono"); desktop invariato.

Direzione scelta e specifica approvata:
`docs/specifiche/2026-10-09-sentinelle-incendi.md` (challenge 2+3 fuse,
Nuxt + FastAPI + PostGIS). Percorso verticale completato (`docs/piani/2026-10-09-percorso-verticale.md`):
dati CFVA in PostGIS, segnalazione dall'app con verifica e motivazioni, coda nel
cruscotto, conferma con punti. Mappa storico con filtro anno (default 2025),
colore per anno e geometrie semplificate precalcolate. Prossimo passo: piano 2, gamification (missioni,
livelli, classifica comuni), poi rifinitura della demo.

Gamification completata (`docs/piani/2026-10-09-gamification.md`): schede
Mappa/Missioni/Classifica, quiz del giorno (12 domande in
`backend/config/quiz.toml`), missioni di posizione, livelli, classifica comuni,
layer "mappature dei cittadini" nel cruscotto. Dati di gioco simulati con
`scripts/semina_demo.py`. Rifinitura: restyling scuro-first con interruttore tema
(`docs/interfaccia/linguaggio-visivo.md`), storico servito come PMTiles
statico (`frontend/public/tiles/storico.pmtiles`, `scripts/genera_tiles.py`),
PostGIS nativo arm64, fonti esterne in parallelo
(`docs/esperimenti/2026-10-09-prestazioni.md`). Mappa base offline Protomaps
(`frontend/public/tiles/sardegna.pmtiles`, 57 MB), proxy `/api` e
`scripts/tunnel.sh` per HTTPS da telefono, stati di errore/caricamento/vuoto,
micro-animazioni, contrasti AA. UI professionale: stile mappa notte
(terra/mare contrastati, limiti sull'estratto), priorità scomposta per fattore
(`fattori` jsonb in segnalazione, `ScomposizionePriorita.vue`), raggi concentrici
22/10/6 + pillole, pin pulsanti (`animaAloni()`), filtro storico nel pulsante livelli (`PulsanteLivelli.vue`, condiviso con il
cruscotto: hotspot e mappature come interruttori, legenda separata dai comandi),
colonna controlli a passo 14 px, popup della mappa come componenti Vue
(`PopupMappa.vue`, `PopupIncendio.vue`, `apriPopup()`), controlli mappa nostri
con icone Lucide (`ControlliMappa.vue`, niente controlli nativi MapLibre), stato
"in diretta" nella pillola dei contatori del cruscotto (`.punto-vivo`).
Storico segnalazioni (`docs/piani/2026-10-10-storico-segnalazioni.md`): `valutata_il`/`punti_ottenuti`, livello "Storico segnalazioni" nel cruscotto con scheda in sola lettura, quarta scheda "Segnalazioni" nell'app con pin per stato e toast alla valutazione (polling 10 s). Prossimo passo: prova su
telefono vero, pitch.

## Chi fa cosa

Ognuno modifica solo la propria riga.

| Persona | Branch | Task corrente | Piano |
|---|---|---|---|
| Alessandro | main | rifinitura demo e pitch | — |
| Nicholas | — | — | — |
| Andrea | — | — | — |
| Nicola | — | — | — |

## Decisioni confermate

- Prova su telefono vero via `scripts/tunnel.sh` riuscita (2026-10-10): mappa,
  tocchi, GPS, fotocamera e aggiornamenti live funzionano. Il problema dei tocchi
  era solo dell'emulazione mobile del browser.

- Memoria condivisa nel repository (`AGENTS.md`, `STATO.md`, `docs/`).
- Metodo: SDD snello, nessun reviewer, una verifica eseguibile per consegna.
- Integrati da cia-sardegna-learning: hook `pre-commit` su STATO.md, piani
  vivi con checkbox, tabella "dove si scrive cosa", `docs/dominio/`,
  `docs/debito.md`.

## Scoperto fuori da un piano

- Fonte incendi principale: WFS regionale
  `https://webgis2.regione.sardegna.it/geoserver/dbu/ows`, layer
  `dbu:areeincendiateperim{2005..2025}`, GeoJSON in EPSG:4326, CORS aperto,
  nessuna chiave. Server instabile: **va precaricato in locale**.
- Tempo quasi reale senza chiave: CSV pubblici NASA FIRMS (Europa, filtro bbox
  Sardegna) e WMS EFFIS (FWI, hotspot, aree bruciate).
- Open-Meteo non fornisce FWI: va calcolato da meteo.
- Lingua: nomi di dominio in italiano, tecnici in inglese (come cia).
- Licenza SardegnaSIRA CC BY-NC-ND: da chiarire prima di usarla.
- Challenge 4 (acqua): i consumi reali non sono pubblici; fattibile solo come
  stato invasi + guasti Abbanoa.

## Da fare prima dell'evento

- [x] Scegliere la direzione di progetto.
- [ ] Condividere specifica e ruoli con Nicholas, Andrea, Nicola.
- [ ] Scegliere il nome dell'app.
- [x] Precaricare perimetri CFVA 2005-2025 e layer pericolo AIB.
- [ ] Decidere come condividere i 280 MB di `dati/` col team (dump o download).
- [ ] Trovare l'URL del bollettino giornaliero di pericolo incendi (Protezione
      Civile Sardegna).
- [ ] Un membro registra la MAP_KEY gratuita NASA FIRMS (solo email).
- [ ] Partecipare al webinar con le domande di `docs/dominio/fonti-incendi.md`.
- [ ] Decidere i ruoli (stack deciso).

## Aperto

- Cruscotto su telefono: provare su telefono vero (tunnel) il trascinamento del
  foglio Segnalazioni, testato solo con gesti simulati.


- Oggi nessun hotspot FIRMS: la demo offline non ne ha; valutare hotspot
  fittizi dichiarati.

- Profilo non tecnico nel team (criterio "gruppo di lavoro").
