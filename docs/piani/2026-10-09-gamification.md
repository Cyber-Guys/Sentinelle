# Gamification: missioni, livelli, classifica dei comuni

> Per agenti: `superpowers:subagent-driven-development` snello (AGENTS.md).
> Spuntare le checkbox, annotare le deviazioni.

**Stato:** completato il 2026-10-09
**Specifica:** `docs/specifiche/2026-10-09-sentinelle-incendi.md`
**Dipende da:** `docs/piani/2026-10-09-percorso-verticale.md` (completato)

**Obiettivo:** rendere l'app viva tutto l'anno: missioni di prevenzione con
punti immediati, livelli, classifica dei comuni; il cruscotto vede cio' che i
cittadini mappano.

## Regole del gioco (decise qui)

| Azione | Punti | Limite |
|---|---|---|
| Segnalazione `fuoco` confermata dall'operatore | +50 | — (gia' implementato) |
| Segnalazione `area_a_rischio` inviata | +10 subito | 3 al giorno |
| Missione `quiz` (quiz del rischio di oggi) | +5 per risposta giusta, max 15 | 1 al giorno |
| Missione `posizione` (punto acqua, sterpaglie, rifiuti a bordo strada) | punti della missione | 3 al giorno per missione |
| Missione `esplora` (scopri gli incendi del tuo comune) | punti della missione | una volta |

Livelli per punti: **Osservatore** 0, **Sentinella** 100, **Guardiano** 300,
**Custode del territorio** 700.

Classifica comuni: somma dei punti degli utenti del comune, con numero di
utenti attivi. Niente normalizzazione per abitanti (dato non caricato).

Dati di demo dichiarati simulati: 20 utenti su 6 comuni con punti e missioni
completate, perche' la classifica non sia vuota in demo.

## Contratti

### Database (aggiunta a `infra/schema.sql`, creata anche da `carica_dati.py` con IF NOT EXISTS)

```sql
CREATE TABLE IF NOT EXISTS missione (id serial PRIMARY KEY, codice text UNIQUE NOT NULL,
  titolo text NOT NULL, descrizione text NOT NULL, punti int NOT NULL,
  tipo text NOT NULL CHECK (tipo IN ('quiz','posizione','esplora')));
CREATE TABLE IF NOT EXISTS missione_completata (id serial PRIMARY KEY,
  utente_id int NOT NULL REFERENCES utente, missione_id int NOT NULL REFERENCES missione,
  punti int NOT NULL, geom geometry(Point,4326), foto text,
  completata_il timestamptz NOT NULL DEFAULT now());
```

Missioni iniziali (seed in `backend/config/missioni.toml`): `quiz_rischio`
(quiz, 15), `punto_acqua` (posizione, 15, "Segnala un punto d'acqua utile ai
mezzi antincendio"), `sterpaglie` (posizione, 20, "Mappa un terreno incolto
con sterpaglie secche"), `rifiuti_strada` (posizione, 15, "Mappa rifiuti
infiammabili a bordo strada"), `esplora_comune` (esplora, 10, "Scopri gli
incendi degli ultimi anni nel tuo comune").

Quiz: `backend/config/quiz.toml`, 12 domande di prevenzione a scelta
multipla (4 opzioni, indice corretto, spiegazione breve). Contenuti generici
e verificabili (numero 1515 del Corpo Forestale, 112, comportamento davanti a
un incendio, mozziconi, barbecue, fasce tagliafuoco). Niente date di divieti
o numeri normativi non verificati. Il quiz del giorno sono 3 domande scelte
in modo deterministico dalla data.

### Logica (`backend/src/sentinelle/gioco.py`, pure dove possibile)

```python
LIVELLI = [("Osservatore", 0), ("Sentinella", 100), ("Guardiano", 300), ("Custode del territorio", 700)]
def livello(punti: int) -> dict   # {nome, soglia, prossima_soglia | None, progresso: 0..1}
def quiz_del_giorno(giorno: date, domande: list[dict]) -> list[dict]
def correggi_quiz(giorno: date, risposte: list[int], domande: list[dict]) -> tuple[int, list[dict]]  # (giuste, esiti con spiegazione)
```

### API (`backend/src/sentinelle/api/gioco.py`)

```text
GET  /utenti/{id}                 -> {id, nome, comune, punti, livello}
GET  /missioni?utente_id=         -> [{id, codice, titolo, descrizione, punti, tipo, disponibile: bool, motivo: str|null}]
GET  /quiz/oggi                   -> [{indice, domanda, opzioni}]   (senza soluzione)
POST /missioni/{id}/completa      multipart: utente_id, lat?, lon?, foto?, risposte? (JSON lista di int)
                                  -> {punti_ottenuti, punti, livello, esiti?}   409 se limite raggiunto
GET  /classifica/comuni           -> [{comune, punti, utenti}] desc, max 20
GET  /classifica/utenti?comune_id= -> [{nome, punti, livello}] desc, max 20
GET  /mappature                   -> GeoJSON delle missioni `posizione` (proprieta': codice, titolo, utente, completata_il)
```

`POST /segnalazioni` con tipo `area_a_rischio`: +10 punti subito se sotto il
limite giornaliero; la risposta include `punti_ottenuti`.

## Task

### Task 1: backend del gioco
- [x] Schema, seed missioni e quiz, `gioco.py`, router `api/gioco.py`, punti su `area_a_rischio`.
- [x] `scripts/semina_demo.py`: 20 utenti simulati su 6 comuni con piu' incendi storici, punti e missioni `posizione` distribuite attorno ai comuni (punti casuali entro 3 km, seed fisso). Idempotente: cancella solo gli utenti con nome marcato `(demo)`. Gli utenti dei 2 comuni base restano.
- [x] `scripts/reset_demo.sql`: azzera anche `missione_completata`.
- **Verifica:** `scripts/prova_gioco.py` via HTTP: quiz con risposte giuste -> punti e livello; secondo quiz stesso giorno -> 409; missione posizione -> punti; area_a_rischio -> +10; classifica comuni non vuota.

### Task 2: frontend del gioco
- [x] `/app`: barra di navigazione in basso con tre schede: **Mappa** (attuale), **Missioni**, **Classifica**. Header con livello e barra di avanzamento verso il prossimo.
- [x] Missioni: card con titolo, punti, stato (disponibile / fatta oggi). `quiz`: 3 domande, esito con spiegazioni. `posizione`: GPS o tocco sulla mappa + foto facoltativa. `esplora`: mostra statistiche del comune (incendi ed ettari per anno, da `/storico/incendi` filtrato) e completa.
- [x] Feedback dei punti: toast "+15 punti", e animazione al cambio di livello.
- [x] Classifica: comuni (evidenziato il proprio) e utenti del proprio comune.
- [x] `/cruscotto`: layer "Mappature dei cittadini" da `/mappature` con icone per tipo, attivabile.
- **Verifica:** browser a 375 px: quiz completo, una missione posizione, classifica aggiornata; cruscotto con il layer delle mappature. Screenshot descritti.

### Task 3: consegna
- [x] README (seed demo, prova gioco), `STATO.md`, deviazioni qui, voci nuove in `docs/debito.md` se tagliamo qualcosa.
- **Verifica:** `prova_percorso.py` e `prova_gioco.py` passano dopo `reset_demo.sql` + `semina_demo.py`.

## Deviazioni

- Task 1: tabelle del gioco in `schema.sql` sotto il marcatore `-- gioco:`; `gioco.prepara_db()` ne esegue il DDL e fa l'upsert delle missioni a ogni avvio dell'app (lifespan); lo stesso DDL gira da `carica_dati.py` e `semina_demo.py`.
- Task 1: "utenti attivi" in classifica = utenti del comune con punti > 0; i comuni senza punti non compaiono.
- Task 1: `POST /segnalazioni` restituisce sempre `punti_ottenuti` (0 per `fuoco` e oltre il limite). Quiz: punti = 5 per risposta giusta anche se 0; `esiti` rivelano la soluzione solo dopo la consegna.
- Task 1: `reset_demo.sql` azzera anche i punti degli utenti demo: rilanciare `semina_demo.py` dopo il reset.
- Task 1: `prova_gioco.py` usa BASE_URL (default :8000), utenti 1 e 2; va rieseguito dopo `reset_demo.sql`.
- Task 2: componenti in `frontend/app/components/` (BarraNavigazione, IndicatoreLivello, ToastPunti, SchedaMissioni, SchedaClassifica); la mappa resta in `app.vue` e si nasconde con `v-show` (resize al ritorno sulla scheda).
- Task 2: missione `posizione` = passaggio alla scheda Mappa in modalita' "scegli punto" (banner, tocco mappa o GPS, foto facoltativa, Conferma/Annulla).
- Task 2: `/utenti/{id}` non espone l'id del comune: la classifica lo ricava da `/comuni` per nome. Statistiche di `esplora` da `/storico/incendi` con bbox attorno al centro del comune (`CENTRI_COMUNI` in `useApi.ts`, 6 comuni demo) filtrate per nome comune.
- Task 2: cruscotto: layer "Mappature dei cittadini" con cerchi colorati per tipo e legenda con icone lucide (nessun simbolo sulla mappa). Il contenitore MapLibre del cruscotto e' ora annidato in un wrapper assoluto (la classe `maplibregl-map` sovrascrive `absolute`).
