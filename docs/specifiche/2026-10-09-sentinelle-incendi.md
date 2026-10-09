# Sentinelle: segnalazione partecipata e gamification contro gli incendi

**Data:** 2026-10-09
**Stato:** approvata
**Challenge:** 2 (prevenzione e smart mapping) + 3 (gamification), fuse.
**Nome:** provvisorio, da decidere col team.

## Problema

Le app di segnalazione incendi falliscono per due motivi: producono falsi
allarmi che nessuno filtra, e si usano solo in emergenza, quindi non sono
installate quando servono. In Sardegna nel 2025 ci sono stati 1362 incendi
>= 1000 mq, ~85% su superfici non boscate: partono dove le persone ci sono.

## Idea

Le comunita' locali diventano sentinelle del proprio territorio tutto l'anno
grazie a missioni di prevenzione; d'estate le loro segnalazioni arrivano agli
operatori gia' verificate (satellite, meteo, vegetazione, storico) e ordinate
per priorita'.

- **Gamification** risolve l'uso tutto l'anno.
- **Verifica incrociata** risolve i falsi allarmi.

Utente principale: comunita' locali (residenti, agricoltori, volontari).
Destinatario delle segnalazioni: operatori (Comune, Barracelli, Protezione
Civile) tramite cruscotto.

## Funzionalita'

### App cittadino (`/app`, PWA)

1. **Mappa del mio comune:** rischio di oggi, incendi storici CFVA,
   segnalazioni attive vicine.
2. **Segnala:** tipo (`fuoco` | `area_a_rischio`), foto, posizione GPS (o tocco
   sulla mappa se GPS negato). Risposta immediata con esito della verifica.
3. **Missioni:** prevenzione tutto l'anno (mappa sterpaglie, verifica punto
   acqua, quiz sul rischio di oggi). Punti immediati.
4. **Profilo e classifica:** punti, livello, classifica dei comuni.

### Cruscotto operatori (`/cruscotto`)

1. Mappa regionale: segnalazioni colorate per priorita', hotspot FIRMS, rischio.
2. Coda ordinata per priorita'; ogni scheda mostra le motivazioni.
3. Azioni: **conferma** o **archivia come falso allarme**.

### Regola del gioco

Le segnalazioni `fuoco` danno punti **solo dopo conferma** dell'operatore; le
missioni danno punti subito. Falsi allarmi non convengono.

## Architettura

```text
frontend/   Nuxt 4 + Tailwind 4 + reka-ui + lucide + MapLibre GL (stack di cia-sardegna-learning)
backend/    FastAPI + SQLAlchemy + GeoAlchemy2
infra/      docker compose: postgis, init dati, backend
dati/       GeoJSON precaricati e versionati
scripts/    scarica_dati.py, prova end-to-end, dump/restore DB
```

Il frontend parla solo con FastAPI, mai con le fonti esterne.

### Moduli backend

| Modulo | Responsabilita' | Dipende da |
|---|---|---|
| `fonti/` | Adattatori FIRMS (CSV pubblico Europa, filtro bbox Sardegna), Open-Meteo, Corine (punto -> classe). Output normalizzato, cache 10 min | rete |
| `rischio/` | Rischio di un punto da meteo + pericolo AIB + vegetazione. Funzione pura | nessuno |
| `verifica/` | Priorita' 0-100 + motivazioni leggibili per una segnalazione | `rischio/`, `fonti/`, PostGIS |
| `segnalazioni/` | Crea, elenca, conferma, archivia; foto su disco | `verifica/` |
| `gioco/` | Missioni, punti, livelli, classifica comuni | eventi di `segnalazioni/` |
| `storico/` | Incendi CFVA per comune/area, statistiche (ettari/anno, conteggi) | PostGIS |

### Modello dati (PostGIS, EPSG:4326)

- `comune(id, nome, geom)`
- `incendio_storico(id, cod_incend, anno, data, comune, ettari_totali, ettari_bosco, tipologia, geom)`
- `pericolo_aib(id, classe, geom)`
- `utente(id, nome, comune_id, punti)` — nessuna password: in demo si sceglie da elenco
- `segnalazione(id, utente_id, tipo, geom, foto, priorita, motivazioni jsonb, stato, creata_il)`
  con `stato` in `nuova | confermata | archiviata`
- `missione(id, titolo, descrizione, punti, tipo)`
- `missione_completata(id, utente_id, missione_id, geom, completata_il)`

### Priorita'

Somma pesata, trasparente, senza ML; pesi in configurazione. Ogni termine
produce una motivazione testuale.

| Termine | Fonte |
|---|---|
| Hotspot FIRMS entro 5 km nelle ultime 24 h | FIRMS |
| Rischio meteo: vento, umidita', giorni senza pioggia | Open-Meteo |
| Vegetazione nel punto | Corine |
| Pericolo AIB della zona | PostGIS |
| Altre segnalazioni entro 2 km nell'ultima ora | PostGIS |
| Incendi storici ricorrenti nell'area | PostGIS |

## Flusso dati

**Offline, prima dell'evento:** `scripts/scarica_dati.py` scarica dal WFS
`https://webgis2.regione.sardegna.it/geoserver/dbu/ows` (`srsName=EPSG:4326`,
`outputFormat=application/json`) perimetri 2005-2025, pericolo AIB e limiti
comunali (layer comunale nel WFS non ancora verificato; fallback: confini
ISTAT), con retry; salva in `dati/`. Fallback: ZIP shapefile annuali
`https://webgis.regione.sardegna.it/scaricocartografiaETL/cfva/areeIncendiatePerim{AAAA}.zip`.
L'init di compose carica i GeoJSON in PostGIS.

**Runtime:** `POST /segnalazioni` -> `verifica` raccoglie fonti -> calcola
priorita' e motivazioni -> salva -> risponde. Il cruscotto fa polling di
`GET /segnalazioni?stato=nuova` ogni 3 s.

## Errori

- Fonte esterna giu': la verifica prosegue, la motivazione lo dichiara, il
  peso si ridistribuisce. Una segnalazione non fallisce mai per una fonte.
- Rete instabile: cache dell'ultimo valore valido; `MODALITA_OFFLINE=1` legge
  FIRMS e meteo da file salvati.
- GPS negato: posizione scelta sulla mappa.

## Demo

Dati live (stagione finita: rischio basso, pochi hotspot) + segnalazioni
simulate su un comune scelto. La demo deve far vedere il **ragionamento**
della verifica, non solo l'esito.

1. Mappa con dati live.
2. Un membro invia una segnalazione dal telefono (piu' segnalazioni simulate
   precaricate nel comune scelto).
3. Il cruscotto la riceve con priorita' e motivazioni.
4. L'operatore conferma: salgono i punti del cittadino e del comune.
5. Chiusura sulle missioni, cioe' l'uso fuori stagione.

## Verifica

- Test mirati solo sulla funzione di priorita' (pura).
- Uno script end-to-end: segnalazione -> verifica -> conferma -> punti.
- Frontend controllato nel browser, desktop e larghezza telefono.

## Fuori perimetro

Autenticazione reale, notifiche push, moderazione foto, integrazione 1515.
Registrati in `docs/debito.md`.
