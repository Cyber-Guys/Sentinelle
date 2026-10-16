# Webapp cittadino (`webapp/`) e stack a tre servizi

Prototipo di riferimento: concept completo G+H della sessione di design del 2026-10-16
(Mappa, Segnala, Località, Avvisi di un luogo, Nuova località, Storico, Profilo). Linguaggio visivo in
`docs/interfaccia/linguaggio-visivo-webapp.md`.

## Architettura

| Servizio compose | Cartella | Cosa fa | Porta |
|---|---|---|---|
| `db` + `dati` | `infra/` | PostGIS, ripristino dump una tantum | interna |
| `backend` | `backend/` | FastAPI, **unico** punto di accesso ai dati, SSE `/eventi` | 8000 (solo localhost) |
| `webapp` | `webapp/` | App cittadino (Nuxt 4 SPA statica + nginx) | 3000 |
| `dashboard` | `frontend/` | Cruscotto operatori **attuale** (da riscrivere), contiene ancora il vecchio `/app` | 3001 |

`webapp` e `dashboard` non parlano mai col database: passano da `/api/**` (nginx -> `backend:8000`). Le
informazioni sono comuni perche' c'e' un solo backend e un solo database: una segnalazione inviata dalla
webapp compare nella coda del cruscotto (stesso `segnalazione`, evento SSE `segnalazione_nuova`).
I tile della mappa (`frontend/public/tiles`, `frontend/public/basemap`) sono montati in sola lettura in entrambi.

## Identita'

Nessuna password (demo): al primo avvio nome e telefono creano un `utente`; l'id sta in `localStorage`
(`sentinelle.utente`). Dal primo avvio si puo' anche entrare con un profilo demo gia' esistente.

## Dati nuovi (idempotenti, in coda a `infra/schema.sql`, dopo `-- gioco:`)

- `utente.telefono text`
- `segnalazione.video text`, `.nota text`, `.direzione int` (gradi 0-359, verso cui guardava l'utente)
- `localita(id, utente_id, nome, tipo casa|terreno|vigna|altro, indirizzo, geom Point, avvisi_attivi bool,
  avvisi_tipi text[] (fuoco|fumo|area_a_rischio), raggio_km int 2|5|10, urgenza urgenti|urgenti_importanti|tutti, creata_il)`

## API nuove (router `backend/src/sentinelle/api/cittadino.py`)

| Metodo e percorso | Corpo / parametri | Risposta |
|---|---|---|
| `POST /utenti` | `{nome, telefono}` | `{id, nome, telefono, ...}` |
| `PATCH /utenti/{id}` | `{nome?, telefono?}` | utente |
| `GET /utenti/{id}/localita` | | `[localita + stato]` |
| `POST /utenti/{id}/localita` | `{nome, tipo, indirizzo?, lat, lon, ...}` | localita + stato |
| `GET /localita/{id}` · `PATCH` · `DELETE` | campi modificabili | localita + stato · 204 |
| `GET /utenti/{id}/avvisi` | | `[{id, priorita, tipo, titolo, testo, localita_id, localita_nome, distanza_km, lat, lon, creato_il}]` ordinati per priorita' |
| `GET /utenti/{id}/storico` | | segnalazioni dell'utente con media, nota, direzione, comune, distanza da casa |
| `GET /luogo?lat&lon` | | `{comune, indirizzo}` (comune offline; via da Nominatim se c'e' rete) |
| `GET /cerca?q=` | | `[{nome, lat, lon}]` (Nominatim; senza rete, comuni del database) |

`stato` di una localita' = `{livello: basso|medio|alto|molto alto, n_zone, zone: GeoJSON (celle 2 km sopra
"medio"), n_segnalazioni, avvisi: n}`; usa la stessa griglia del "Rischio di oggi" del cruscotto.

Avvisi (priorita' `urgente` > `importante` > `informazione`), per localita' con avvisi attivi:
fuoco entro 2 km = urgente; fuoco o fumo entro `raggio_km` = importante; area a rischio entro
`raggio_km` e rischio alto o molto alto oggi = informazione. Filtrati da `avvisi_tipi` e `urgenza`.

Cambia `POST /segnalazioni` (resta compatibile col vecchio `/app`): campi facoltativi `video` (file),
`nota`, `direzione`; le risposte aggiungono `video_url`, `nota`, `direzione`. I media si leggono da `/foto/{nome}`.

## Fuori da questa consegna (debito)

Notifiche push a app chiusa (serve service worker + VAPID), login vero, cancellazione di una segnalazione,
modifica di nome o tipo di una localita' gia' salvata, tema scuro, versione tablet.
