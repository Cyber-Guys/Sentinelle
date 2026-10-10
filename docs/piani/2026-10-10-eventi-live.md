# Aggiornamenti live con SSE e LISTEN/NOTIFY

> Per agenti: SDD snello (AGENTS.md). Spuntare le checkbox, annotare le deviazioni.

**Stato:** completato

**Obiettivo:** app e cruscotto si aggiornano all'istante quando cambia qualcosa
(segnalazioni, valutazioni, mappature, hotspot), senza polling fitto. Gli
eventi nascono nel database, quindi funzionano con piu' processi backend.

## Contratti

### Database (infra/schema.sql, sezione eseguita all'avvio)
- Funzione `notifica_sentinelle()` + trigger:
  - `segnalazione` AFTER INSERT -> `{"tipo":"segnalazione_nuova","id","utente_id","priorita"}`
  - `segnalazione` AFTER UPDATE OF stato (quando cambia) -> `{"tipo":"segnalazione_valutata","id","utente_id","stato"}`
  - `missione_completata` AFTER INSERT con geom non nulla -> `{"tipo":"mappatura_nuova","id","utente_id"}`
- Canale unico: `pg_notify('sentinelle', json)`.
- Hotspot: un task in background del backend riscarica FIRMS ogni 10 min; se
  l'insieme cambia esegue `SELECT pg_notify('sentinelle', '{"tipo":"hotspot_aggiornati","n":N}')`.

### Backend
- All'avvio (lifespan FastAPI): una connessione `psycopg.AsyncConnection` in
  autocommit fa `LISTEN sentinelle` e inoltra ogni notifica a tutti gli iscritti
  (una `asyncio.Queue` per client, scarto se piena). Riconnessione con attesa se
  la connessione cade.
- `GET /eventi` -> `text/event-stream`: `event: <tipo>\ndata: <json>\n\n`,
  commento di heartbeat ogni 15 s, header `Cache-Control: no-cache`,
  `X-Accel-Buffering: no`. Evento iniziale `event: pronto`.
- Nessun dato sensibile negli eventi: solo id e campi elencati; i dettagli si
  leggono dalle API esistenti.

### Frontend
- Composable `useEventi()`: una sola `EventSource('/api/eventi')` condivisa,
  stato `connesso | riconnessione`, sottoscrizione per tipo.
- Cruscotto: `segnalazione_nuova` -> ricarica coda; `segnalazione_valutata` ->
  coda + valutate; `mappatura_nuova` -> mappature; `hotspot_aggiornati` -> hotspot.
- App: `segnalazione_valutata` con il proprio `utente_id` -> ricarica le proprie
  (toast gia' esistente); `hotspot_aggiornati` -> hotspot.
- Polling attuale ridotto a rete di sicurezza ogni 30 s. Pillola di stato del
  cruscotto: "In diretta" se connesso, "Riconnessione..." (ambra) altrimenti;
  niente piu' "ogni 3 s".

## Task

### Task 1: backend
- [x] Trigger e funzione, listener, `/eventi`, task hotspot.
- **Verifica:** `curl -N localhost:8000/eventi` riceve `pronto`; un POST
  /segnalazioni, una conferma e una missione posizione producono i tre eventi;
  `prova_percorso.py` e `pytest` verdi.

### Task 2: frontend
- [x] `useEventi`, reazioni in cruscotto e app, polling a 30 s, pillola di stato.
- [x] Verifica che lo stream passi dal proxy Nitro `/api` senza buffering.
- **Verifica:** cruscotto aperto, segnalazione inviata via curl: compare in
  coda in meno di 1 s; valutazione dal cruscotto: toast nell'app in meno di 1 s.

### Task 3: consegna
- [x] Esperimento breve in `docs/esperimenti/` (latenza prima/dopo, richieste al
  minuto per client prima/dopo), STATO.md.

## Deviazioni

Task 1: codice in `backend/src/sentinelle/eventi.py`; DDL in coda alla sezione `-- gioco:` (eseguita come unico statement, `$$` non richiede split). Il payload JSON dei trigger ha spazi attorno ai `:` (json_build_object), innocuo.

Task 2: nessuna rotta Nitro dedicata: il proxy routeRules `/api/**` inoltra l'SSE senza buffering (`pronto` a 0.01 s). `useEventi` espone `{ on, stato }` con `stato` `connesso|riconnessione`; chiude l'EventSource senza iscritti. Estratte `caricaHotspot()` in app e cruscotto. Task 3: misure in `docs/esperimenti/2026-10-10-eventi-live.md`.
