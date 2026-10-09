# Stato del lavoro

> **Riferimento:** nessun commit — 2026-10-09

## Fase

Preparazione pre-hackathon (evento 16-17 ottobre, webinar 14 ottobre).
Materiali e criteri di valutazione sintetizzati in `docs/materiali/README.md`.
Fonti dati analizzate e verificate in `docs/dominio/fonti-*.md`.

Direzione scelta e specifica approvata:
`docs/specifiche/2026-10-09-sentinelle-incendi.md` (challenge 2+3 fuse,
Nuxt + FastAPI + PostGIS). Percorso verticale completato (`docs/piani/2026-10-09-percorso-verticale.md`):
dati CFVA in PostGIS, segnalazione dall'app con verifica e motivazioni, coda nel
cruscotto, conferma con punti. Mappa storico con filtro anno (default 2025),
colore per anno e geometrie semplificate precalcolate. Prossimo passo: piano 2, gamification (missioni,
livelli, classifica comuni), poi rifinitura della demo.

## Chi fa cosa

Ognuno modifica solo la propria riga.

| Persona | Branch | Task corrente | Piano |
|---|---|---|---|
| Alessandro | main | piano gamification | — |
| Nicholas | — | — | — |
| Andrea | — | — | — |
| Nicola | — | — | — |

## Decisioni confermate

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

- Errore in console di `@lucide/vue` (useLucideProps): icone funzionanti, da
  risolvere.
- PostGIS gira in emulazione amd64 (nessuna immagine arm64 ufficiale): query
  di vicinanza ~1-2 s. Alternativa: immagine arm64 non ufficiale.
- Oggi nessun hotspot FIRMS: la demo offline non ne ha; valutare hotspot
  fittizi dichiarati.

- Profilo non tecnico nel team (criterio "gruppo di lavoro").
