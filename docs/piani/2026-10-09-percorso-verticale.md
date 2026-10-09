# Percorso verticale: segnalazione verificata dall'app al cruscotto

> Per agenti: eseguire con `superpowers:subagent-driven-development` in
> modalita' snella (AGENTS.md). Spuntare le checkbox man mano; annotare le
> deviazioni qui.

**Stato:** completato il 2026-10-09
**Specifica:** `docs/specifiche/2026-10-09-sentinelle-incendi.md`

**Obiettivo:** il percorso minimo completo della demo: dati CFVA in PostGIS,
segnalazione dall'app, verifica con priorita' e motivazioni, coda nel
cruscotto, conferma dell'operatore. La gamification e' nel piano successivo.

**Stack:** PostGIS 17 in docker compose; Python 3.12 in conda env
`sentinelle` (FastAPI, SQLAlchemy 2, GeoAlchemy2, psycopg 3, httpx, pytest);
Nuxt 4 + Tailwind 4 + reka-ui + lucide + maplibre-gl (stack di
`cia-sardegna-learning/frontend`).

**Lingua:** nomi di dominio in italiano (`segnalazione`, `priorita'`,
`motivazioni`), vocabolario tecnico in inglese, come in cia-sardegna-learning.

**Prerequisito:** Docker Desktop avviato.

## Struttura file

```text
infra/compose.yaml                 postgis (porta 5432, volume nominato)
infra/schema.sql                   tabelle della specifica, montato in /docker-entrypoint-initdb.d
scripts/scarica_dati.py            WFS -> dati/*.geojson (una volta, poi versionati)
scripts/carica_dati.py             dati/*.geojson -> PostGIS (idempotente)
scripts/prova_percorso.py          prova end-to-end via HTTP
dati/                              GeoJSON EPSG:4326
backend/pyproject.toml
backend/src/sentinelle/config.py   pydantic-settings: DATABASE_URL, MODALITA_OFFLINE, CORS
backend/src/sentinelle/db.py       engine e sessione
backend/src/sentinelle/main.py     app FastAPI, CORS localhost:3000, router
backend/src/sentinelle/fonti/      firms.py, meteo.py, corine.py, cache.py
backend/src/sentinelle/rischio.py  funzione pura
backend/src/sentinelle/verifica.py priorita' (pura) + raccolta contesto (I/O)
backend/src/sentinelle/api/        segnalazioni.py, storico.py
backend/config/pesi.toml           pesi della priorita'
backend/tests/test_verifica.py     unici test: priorita' e rischio
frontend/                          Nuxt 4: pages/app/index.vue, pages/cruscotto/index.vue
```

## Contratti

### Database (`infra/schema.sql`)

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE comune (id serial PRIMARY KEY, nome text NOT NULL, geom geometry(MultiPolygon,4326));
CREATE TABLE incendio_storico (id serial PRIMARY KEY, cod_incend text, anno int, data date,
  comune text, ettari_totali double precision, ettari_bosco double precision,
  tipologia text, geom geometry(MultiPolygon,4326));
CREATE TABLE pericolo_aib (id serial PRIMARY KEY, classe text, geom geometry(MultiPolygon,4326));
CREATE TABLE utente (id serial PRIMARY KEY, nome text NOT NULL, comune_id int REFERENCES comune, punti int NOT NULL DEFAULT 0);
CREATE TABLE segnalazione (id serial PRIMARY KEY, utente_id int REFERENCES utente,
  tipo text NOT NULL CHECK (tipo IN ('fuoco','area_a_rischio')),
  geom geometry(Point,4326) NOT NULL, foto text, priorita int NOT NULL,
  motivazioni jsonb NOT NULL, stato text NOT NULL DEFAULT 'nuova'
  CHECK (stato IN ('nuova','confermata','archiviata')), creata_il timestamptz NOT NULL DEFAULT now());
-- indici GIST su tutte le geom
```

### Fonti (`fonti/`)

```python
@dataclass(frozen=True)
class Hotspot: lat: float; lon: float; rilevato_il: datetime; confidenza: str

@dataclass(frozen=True)
class Meteo: vento_kmh: float; raffiche_kmh: float; umidita: float; temperatura: float; giorni_senza_pioggia: int

def hotspot_sardegna() -> list[Hotspot] | None        # None = fonte non disponibile
def meteo(lat: float, lon: float) -> Meteo | None
def classe_suolo(lat: float, lon: float) -> tuple[int, str] | None   # (codice CLC, descrizione)
```

- FIRMS: `https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Europe_24h.csv`
  (e NOAA-20 analogo), filtro bbox lon 8-10, lat 38.8-41.3.
- Open-Meteo: `https://api.open-meteo.com/v1/forecast` con hourly
  `temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m`; giorni
  senza pioggia da `https://archive-api.open-meteo.com/v1/archive`
  (`daily=precipitation_sum`, ultimi 30 giorni, soglia 1 mm).
- Corine: `https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/identify`
  con punto in EPSG:3857 (`sr=102100`); conversione lon/lat -> 3857 in Python.
- Cache in memoria 10 min per chiave; su errore restituisce l'ultimo valore
  valido, altrimenti `None`. Timeout 5 s.
- `MODALITA_OFFLINE=1`: legge da `dati/offline/{firms.csv,meteo.json,corine.json}`.

### Priorita' (`rischio.py`, `verifica.py`, funzioni pure)

```python
def rischio_meteo(m: Meteo) -> float   # 0..1

@dataclass(frozen=True)
class Contesto:
    hotspot_km: float | None          # distanza dal piu' vicino, None = fonte giu'
    meteo: Meteo | None
    classe_suolo: tuple[int, str] | None
    pericolo_aib: str | None          # classe della zona, None = fuori layer
    segnalazioni_vicine: int          # entro 2 km, ultima ora
    incendi_storici: int              # entro 1 km, 2005-2025

@dataclass(frozen=True)
class Esito: priorita: int; motivazioni: list[str]   # 0..100

def calcola_priorita(c: Contesto, pesi: dict[str, float]) -> Esito
```

Regole: ogni termine vale 0..1 moltiplicato per il suo peso; i termini con
fonte `None` sono esclusi e i pesi restanti rinormalizzati a somma 1; ogni
termine aggiunge una motivazione leggibile ("Hotspot satellitare a 1,2 km",
"Satellite non disponibile"). Pesi iniziali in `pesi.toml`: hotspot 0.30,
meteo 0.25, suolo 0.15, pericolo 0.10, vicine 0.10, storico 0.10.

### API

```text
GET  /salute                         -> {"ok": true}
GET  /comuni                         -> [{id, nome}]
GET  /utenti                         -> [{id, nome, comune, punti}]
POST /segnalazioni   multipart: utente_id, tipo, lat, lon, foto?   -> Segnalazione
GET  /segnalazioni?stato=nuova       -> [Segnalazione] ordinate per priorita' desc
POST /segnalazioni/{id}/conferma     -> Segnalazione
POST /segnalazioni/{id}/archivia     -> Segnalazione
GET  /hotspot                        -> GeoJSON FeatureCollection
GET  /rischio?lat=&lon=              -> {valore: 0..1, livello: basso|medio|alto, meteo: Meteo|null}
GET  /storico/incendi?bbox=minlon,minlat,maxlon,maxlat&anno_da=2015  -> GeoJSON
GET  /foto/{nome}                    -> file

Segnalazione = {id, utente_id, tipo, lat, lon, foto_url, priorita, motivazioni: [str], stato, creata_il}
```

## Task

### Task 1: infrastruttura e schema
- [x] `infra/compose.yaml` (immagine `postgis/postgis:17-3.5`, utente/password/db `sentinelle`, volume nominato, `schema.sql` in initdb), `.env.example` con `DATABASE_URL=postgresql+psycopg://sentinelle:sentinelle@localhost:5432/sentinelle`.
- **Verifica:** `docker compose -f infra/compose.yaml up -d` e `psql` che elenca le 5 tabelle e `postgis_version()`.

### Task 2: scaricamento dati
- [x] `scripts/scarica_dati.py`: WFS `https://webgis2.regione.sardegna.it/geoserver/dbu/ows`, `service=WFS&version=2.0.0&request=GetFeature&typeNames=<layer>&outputFormat=application/json&srsName=EPSG:4326`, retry 3 volte con attesa crescente, timeout 120 s. Layer: `dbu:areeincendiateperim{2005..2025}`, `dbu:exp_pericolo_23`. Comuni: cercare il layer dei limiti comunali nel GetCapabilities; se assente, confini ISTAT generalizzati filtrati sulla Sardegna. Salva `dati/perimetri_{anno}.geojson`, `dati/pericolo_aib.geojson`, `dati/comuni.geojson`. Salta i file gia' presenti.
- [x] Generare `dati/offline/` con un'istantanea di FIRMS, meteo e Corine per 3 punti di prova.
- **Verifica:** elenco file con dimensione e numero di feature per file.

### Task 3: caricamento in PostGIS
- [x] `scripts/carica_dati.py`: legge i GeoJSON, `ST_Multi(ST_GeomFromGeoJSON(...))`, mappa i campi CFVA (`COD_INCEND`, `DATA` gg/mm/aaaa, `COMUNE`, `TOTALE_HA`, `BOSCO_HA`, `TIPOLOGIA`), svuota e ricarica (idempotente). Crea 5 utenti di demo in 2 comuni.
- **Verifica:** conteggi per tabella; 1362 incendi per il 2025.

### Task 4: backend base e storico
- [x] Conda env `sentinelle` (Python 3.12), `pyproject.toml`, `config.py`, `db.py`, `main.py`, endpoint `/salute`, `/comuni`, `/utenti`, `/storico/incendi`.
- **Verifica:** `uvicorn sentinelle.main:app` + `curl` su `/storico/incendi` con bbox di un comune, numero di feature.

### Task 5: fonti esterne
- [x] `fonti/` secondo il contratto, con cache e modalita' offline. Endpoint `/hotspot`.
- **Verifica:** script inline che stampa hotspot in Sardegna, meteo e classe suolo per un punto; poi stesso output con `MODALITA_OFFLINE=1`.

### Task 6: priorita' (TDD)
- [x] `tests/test_verifica.py`: contesto massimo -> priorita' alta; contesto minimo -> bassa; una fonte `None` -> esclusa, pesi rinormalizzati, motivazione "non disponibile"; numero di motivazioni pari ai termini.
- [x] `rischio.py`, `verifica.calcola_priorita`, `config/pesi.toml`.
- **Verifica:** `pytest backend/tests -q` verde.

### Task 7: API segnalazioni
- [x] `verifica.raccogli_contesto(sessione, lat, lon) -> Contesto` (query PostGIS con `ST_DWithin` su geography + fonti) e endpoint del contratto, incluso `/rischio`. Foto salvate in `backend/foto/` (ignorata da Git). Conferma: `+50` punti all'utente se tipo `fuoco`; archivia: nessun punto.
- **Verifica:** `scripts/prova_percorso.py`: crea segnalazione, la trova in coda con motivazioni, la conferma, controlla i punti.

### Task 8: frontend base e app cittadino
- [x] Nuxt 4 in `frontend/` con lo stack di cia (copiare `package.json` e configurazione Tailwind da `cia-sardegna-learning/frontend`, togliere cio' che non serve), `maplibre-gl`, composable `useApi` con `NUXT_PUBLIC_API_BASE_URL`. Manifest PWA minimo.
- [x] `/app`: scelta utente da elenco; mappa (base OSM raster) centrata sul comune con incendi storici e hotspot; badge "rischio di oggi" da `/rischio`; pulsante "Segnala" -> tipo, foto (`<input type=file accept=image/* capture=environment>`), posizione GPS o tocco sulla mappa; esito con priorita' e motivazioni.
- **Verifica:** browser a larghezza telefono: invio di una segnalazione e esito visibile; screenshot.

### Task 9: cruscotto operatori
- [x] `/cruscotto`: mappa regionale (segnalazioni colorate per priorita', hotspot), coda con polling 3 s, scheda con motivazioni e foto, pulsanti conferma/archivia.
- **Verifica:** due finestre, app e cruscotto: la segnalazione compare entro 3 s, la conferma la toglie dalla coda e aggiorna i punti.

### Task 10: avvio e consegna
- [x] `README.md` con avvio in 3 comandi (compose, backend, frontend), `.claude/launch.json` per backend e frontend, `.gitignore` aggiornato (`backend/foto/`), aggiornamento `STATO.md` e struttura in `AGENTS.md`.
- **Verifica:** da clone pulito, i 3 comandi portano alla demo funzionante.

## Deviazioni

- Task 1: l'immagine `postgis/postgis:17-3.5` non ha build arm64: aggiunto `platform: linux/amd64` (emulazione) in `infra/compose.yaml`.
- Task 2: comuni da WFS `dbu:limiti_amministr_com_ctr` (campo `nome`), non ISTAT. FIRMS offline: l'istantanea contiene solo l'header (nessun hotspot in Sardegna nelle ultime 24h). Env conda `sentinelle` con anche pyproj e pyshp (non usati).
- Task 3: i GeoJSON hanno coordinate 3D e campi diversi per anno (2005-2006 senza comune, date e unita' variabili): mappatura con campi alternativi, `ST_Force2D` e `ST_CollectionExtract`. Pericolo AIB: campo `valore` (Basso..Alto). 2105 incendi con data/ettari/comune mancanti. Utenti demo: SERRAMANNA e VILLASOR.
- Task 4-7: avvio backend con `uvicorn sentinelle.main:app --app-dir src` da `backend/` (pacchetto installato in editable). `anno_da` di `/storico/incendi` ha default 2005. Corine identify restituisce solo il codice (`Code_18`): le descrizioni vengono da un dizionario CLC in `fonti/corine.py`. Cache meteo a griglia 0,01 gradi. `hotspot_km` = 999 se la fonte risponde ma non ci sono hotspot (motivazione "nessun hotspot entro 10 km"); `None` solo se la fonte e' giu'. `pericolo_aib=None` (fuori layer) vale 0 ma resta come termine. `raccogli_contesto` sta in `verifica.py` con `calcola_priorita`; pesi letti da `pesi.toml` a livello di modulo.
- Task 8-9: `ssr: false`; lucide-vue fissato a 1.34.0 (la 1.54 rompe l'inject delle props con Nuxt); niente service worker. Il centro del comune per `/rischio` e' una tabella fissa SERRAMANNA/VILLASOR nel frontend (l'API non espone coordinate dei comuni). Storico ricaricato per bbox visibile a ogni `moveend` (anno_da=2015). Cruscotto: nessun hotspot ancora visibile (API vuota); 'Falso allarme' = archivia.
- Task 10: `scripts/reset_demo.sql` per riportare la demo a zero. Correzione del controller: le segnalazioni archiviate non contano piu' tra le "vicine".
- Storico (post piano): `incendio_storico.geom_semplice` precalcolata (0.0005) con indice GIST, creata anche via `ALTER TABLE IF NOT EXISTS` in `carica_dati.py`; `/storico/incendi` la usa e accetta `anno_a` (default 2025) e include `anno`. App cittadino: filtro 2025 (default) / Ultimi 5 anni / Dal 2015, colore per anno, riempimento 0,35, ricarica con debounce 300 ms e indicatore di caricamento (sostituisce `anno_da=2015` fisso).
