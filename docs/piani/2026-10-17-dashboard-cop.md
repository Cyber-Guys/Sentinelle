# Dashboard COP (operatori)

Obiettivo: riprogettare il cruscotto operatori come `/dashboard` per i 7 COP della Sardegna.
Concept approvato in brainstorming (2026-10-17): impianto B (ingresso con le 7 aree, zoom animato
sull'area scelta) + pannello statistiche fisso a destra come nell'impianto A. Demo su laptop: i dati
che non abbiamo si simulano e lo si dichiara nell'interfaccia.

## Decisioni

- **Aree COP:** 7 aree con sede nei servizi territoriali CFVA (Cagliari, Iglesias, Oristano, Nuoro,
  Lanusei, Sassari, Tempio). Confini approssimati: ogni comune va alla sede piu' vicina, poi unione e
  smussatura in PostGIS. Da dichiarare come approssimazione.
- **Rischio = bollettino CFD simulato** (verde/arancione/rosso, emesso il giorno prima). Forme morbide
  ottenute con buffer positivo/negativo in metri. Il ricalcolo del rischio da FIRMS/meteo/Corine
  (`/rischio/griglia`, `/aree-critiche`) resta commentato: la dashboard non lo usa.
- **Incendi attivi:** segnalazioni certificate non spente + alcuni incendi simulati (stato in memoria,
  si azzera al riavvio del backend). "Concludi incendio" -> area bruciata visibile come spenta per 72 h.
- **Vedette e fuochi autorizzati:** simulati, deterministici. Stazioni = basi reali (`/basi`). Mezzi =
  flotta simulata esistente (`/flotta`). Invasi = dati reali CeDoc (`/invasi`).
- **Segnalazioni:** l'operatore guarda solo le foto pertinenti (punteggio "AI" simulato, non
  implementato) e i segnali di validazione gia' calcolati (segnalazioni congiunte, conferme dei vicini,
  affidabilita'). "Certifica" = `conferma` esistente: l'app cittadino la vede subito come incendio,
  piu' il conteggio delle persone avvisate entro 5 km.
- Implementazione inline del controller (niente implementer subagent): il lavoro e' quasi tutto
  frontend e la qualita' visiva dipende dalle skill caricate nella sessione.

## File

- `backend/src/sentinelle/cop.py`, `backend/src/sentinelle/api/cop.py`, `main.py` (router)
- `backend/src/sentinelle/api/scenario.py` (route di ricalcolo del rischio commentate)
- `scripts/semina_cop.py` + `dati/demo_foto/` (segnalazioni demo con foto)
- `frontend/app/pages/dashboard.vue`, `frontend/app/pages/cruscotto.vue` (redirect), `frontend/app/composables/useCop.ts`,
  `frontend/app/components/cop/*`
- `scripts/docker.sh`, `compose.yaml`, `README.md`, `frontend/app/pages/index.vue` (link)

## Contratti API (nuovi, prefisso `/cop`)

- `GET /cop/aree` -> FeatureCollection, properties `{id, nome, centro:[lon,lat], bbox:[o,s,e,n], comuni}`
- `GET /cop/bollettino?giorno=oggi|domani` -> `{emesso_il, valido_per, simulato:true, zone: FeatureCollection(livello verde|arancione|rosso), per_area: {id: {verde, arancione, rosso}}}` (quote 0-1)
- `GET /cop/vedette` -> FeatureCollection punti `{id, nome, area, raggio_km, stato}`
- `GET /cop/fuochi` -> FeatureCollection punti `{id, comune, tipo, data, dalle, alle, ettari, stato}`
- `GET /cop/incendi` -> FeatureCollection poligoni `{id, nome, comune, stato attivo|spento, inizio, spento_il, ettari, fronte_m, origine:'simulato'|'segnalazione'}`
- `POST /cop/incendi/{id}/concludi` -> incendio aggiornato
- `GET /cop/statistiche?area=` -> `{mesi_media:[12], mesi_2025:[12], anni:[{anno, incendi, ettari}]}`
- `POST /cop/segnalazioni/{id}/certifica` -> segnalazione + `{avvisati}`

## Task

- [x] 1. Backend `/cop/*` + seed segnalazioni demo con foto (`scripts/semina_cop.py`, foto in `dati/demo_foto/`)
- [x] 2. Frontend: ingresso aree + zoom, mappa con layer, pannello statistiche
- [x] 3. Frontend: vista Segnalazioni (foto, validazione, certifica / falso allarme)
- [x] 4. Concludi incendio, rinomina `/cruscotto` -> `/dashboard`, docker e README
- [x] 5. Verifica nel browser (1440 px e telefono) + build Docker statico: ingresso, zoom, pannello, scheda incendio, concludi, certificazione (app la vede come "operatori", 20 avvisati). Tema chiaro non provato
- [x] 6. Bollettino generato fuori dal server (deviazione, sotto)

## Deviazione: bollettino precalcolato (2026-10-17)

Il calcolo del bollettino (~10 s e molta RAM per giorno, buffer su tutta l'isola) insieme a dev server e browser
ha bloccato due volte il portatile di sviluppo (WSL con 7 GB). Ora il backend non lo calcola mai: legge
`dati/bollettini/bollettino-AAAA-MM-GG.json` e `aree-cop.json`, generati con `./scripts/docker.sh bollettini 7`
su un PC capiente e committati (guida nel README). Giorno mancante -> file piu' vicino (`ripiego_da`);
nessun file -> nessuna zona, tutto verde (`mancante: true`).

Bollettini 17-23 ottobre generati da un collega e committati (`dati/bollettini/`).

## Scelte fatte in verifica

- Segnalazioni certificate entro 2,5 km = un solo incendio (`segnalazioni` nelle proprieta'); "concluso" chiude tutto il gruppo.
- Coda ordinata per priorita' + segnalazioni congiunte + conferme - smentite; badge contati per gruppo.
- Mezzo libero oltre 45 min: avviso "nessun mezzo libero entro 45 min" invece del tempo.
- Foto non della demo: "classificazione incerta" (il modello AI e' simulato solo sulle foto demo).
- `semina_cop.py` aggiunge residenti con una localita' monitorata: il conteggio degli avvisati non e' zero.
- Telefono: pannello come foglio in basso, mappa inquadrata sopra.
- Mappa base satellitare predefinita (Esri World Imagery, online) con etichette Protomaps; stradale offline come
  alternativa; senza rete ritorno automatico alla stradale (provato con il browser offline).

## Da fare

- Provare il tema chiaro; merge su `main` dopo una prova del team.
- Dopo una demo: `./scripts/docker.sh exec -T backend python scripts/semina_cop.py` ripristina le segnalazioni.

## Verifica

`./scripts/docker.sh` poi http://localhost:3001/dashboard: scelta area, zoom, layer, statistiche,
certificazione di una segnalazione visibile nell'app cittadino (http://localhost:3000).
