# Eventi live (SSE): latenza e richieste

Setup: cruscotto in Chrome 1440x900 tema scuro, backend :8000, Nuxt dev :3000 (proxy `/api`). Eventi misurati con MutationObserver sul DOM e `Date.now()`.

## Latenza (azione -> comparsa a schermo)

| Azione | Prima (polling) | Dopo (SSE) |
|---|---|---|
| POST /segnalazioni -> contatore "in coda" nel cruscotto | 0-3 s (media 1.5 s) | 0.67 s dall'inizio della POST, 0.11 s dopo la risposta (la POST impiega 0.55 s) |
| conferma dal cruscotto -> toast nell'app (scheda in background) | 0-10 s | 0.04 s dall'inizio della POST |
| missione posizione completata -> contatore mappature | 0-5 s | 0.16 s |
| Stream via proxy Nitro | - | `pronto` a 0.01 s, evento a 0.14 s dalla POST: nessun buffering |

## Richieste di rete al minuto (cruscotto inattivo)

- Prima, dal codice: aggiorna ogni 3 s = 20 x 2 richieste (coda + confermate) + mappature ogni 5 s = 12 + valutate ogni 10 s = 6 (solo con scheda non "In coda") = 52-58/min. App: 6/min (proprie ogni 10 s).
- Dopo, misurato 66 s (performance.getEntriesByType): 6 richieste (4 segnalazioni + 2 mappature) = circa 5.5/min, piu' 1 connessione SSE aperta. App: 2/min.

## Pillola di stato

EventSource forzato in errore: "In diretta" -> "Riconnessione..." con `.punto-ambra`. Console pulita dopo reload su scheda nuova.

## Comandi

```bash
curl -sN localhost:3000/api/eventi
curl -X POST localhost:8000/segnalazioni -F utente_id=1 -F tipo=fuoco -F lat=39.42 -F lon=8.93
curl -X POST localhost:8000/segnalazioni/<id>/conferma
curl -X POST localhost:8000/missioni/7/completa -F utente_id=1 -F lat=39.2 -F lon=9.1
cd frontend && npm run build
```
