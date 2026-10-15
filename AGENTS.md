# AGENTS.md

Fonte unica delle convenzioni per qualunque agente (Claude Code, Codex, Gemini,
Cursor, Copilot) e per ogni membro del team. `CLAUDE.md` e `GEMINI.md` rimandano
qui: le regole si modificano solo in questo file, cosi' le guide non divergono.

> **Un agente alla volta per working tree.** Due sessioni attive sulla stessa
> copia si sovrascrivono le modifiche non committate senza accorgersene. Per
> lavorare in parallelo sulla stessa macchina serve un `git worktree` separato.

## Primo avvio in un nuovo clone

Una volta per clone, dalla radice del repository:

1. `./scripts/setup.sh`: verifica i prerequisiti (stampa cosa manca e come
   installarlo), attiva gli hook, crea l'ambiente Python (conda, altrimenti uv,
   altrimenti `backend/.venv`), `npm ci`, avvia PostGIS e carica i dati demo.
   Idempotente: in caso di dubbio si rilancia. Deve finire con `Pronto.` e i
   conteggi 377 comuni / 27544 incendi.
2. Avvio: `./scripts/avvia.sh` (backend + frontend, Ctrl+C ferma), oppure in
   Claude Code `.claude/launch.json` (`backend`, `frontend`). Entrambi passano
   per `scripts/backend.sh`, che trova da solo l'ambiente Python.
3. Verifica: `curl localhost:8000/salute` risponde `{"ok":true}` e
   http://localhost:3000/app mostra la mappa.

Comandi Python del progetto sempre con `./scripts/python.sh <script>`: funziona
con conda e con venv. Problemi frequenti e guida per le persone in
`ONBOARDING.md`.

## Come lavorare qui da agente

Il flusso, in ordine; i dettagli sono nelle sezioni indicate.

- **Inizio sessione:** leggi `STATO.md` e verifica i commit successivi al
  riferimento ("Prima cosa da fare in ogni sessione"). La parola chiave
  **«riprendi»** fa solo questo, senza modificare nulla.
- **Branch:** uno per persona o feature (`nome/feature`), merge piccoli e
  frequenti su `main` ("Lavoro in team"). Un agente per working tree.
- **Lavoro:** SDD snello, un implementer alla volta, nessun reviewer, una
  verifica eseguibile per consegna ("Implementazione", "Economia del
  progetto"). Ogni contenuto nella cartella giusta ("Dove si scrive cosa").
- **Fine sessione:** la parola chiave **«consegna»** aggiorna `STATO.md` (SHA di
  riferimento e solo la propria riga in "Chi fa cosa") e propone il commit
  ("Consegna e ripresa"). Commit e push solo su richiesta.

## Prima cosa da fare in ogni sessione

1. Leggi `STATO.md`.
2. Allinea il branch e verifica i commit successivi al riferimento dello stato:

   ```bash
   git pull --rebase
   git log --oneline $(grep -m1 -oE '[0-9a-f]{7,40}' STATO.md)..HEAD
   ```

   Se elenca commit che toccano il codice, `STATO.md` e' piu' vecchio di quelle
   modifiche: leggi quei commit prima di fidarti di cio' che dice.
3. Se in `STATO.md` c'e' un piano attivo associato al tuo task, aprilo in
   `docs/piani/` prima di modificare codice.

Alla fine della sessione aggiorna `STATO.md` prima dell'ultimo commit (vedi
"Consegna e ripresa").

## Obiettivo

Hackathon a tema incendi, lavoro di gruppo. Challenge e vincoli ufficiali in
`docs/materiali/` (sintesi in `docs/materiali/README.md`).

**Sentinelle** (nome provvisorio), challenge 2 + 3 fuse: le comunita' locali
diventano sentinelle del territorio tutto l'anno grazie a missioni di
prevenzione (gamification); d'estate le loro segnalazioni arrivano agli
operatori gia' verificate (satellite FIRMS, meteo, vegetazione Corine, storico
CFVA) e ordinate per priorita'. Due interfacce: app cittadino (`/app`, da
telefono) e cruscotto operatori (`/cruscotto`). Specifica
`docs/specifiche/2026-10-09-sentinelle-incendi.md`, decisione
`docs/decisioni/2026-10-09-direzione-e-architettura.md`.

## Mantra

**Demo funzionante prima di tutto.** Si vince con una demo end-to-end che gira
davanti alla giuria e una storia chiara, non con codice robusto. Ogni scelta si
giudica con una domanda: *questo si vede nella demo o nel pitch?* Se no, non si
fa.

- Prima un percorso verticale completo e brutto (dato -> elaborazione ->
  output visibile), poi si migliora un pezzo alla volta.
- Dati finti o mock sono ammessi se dichiarati; mai bloccare la demo per un
  dato mancante.
- Tutto deve girare in locale con un solo comando, senza dipendere dalla rete
  della sala se evitabile.

La giuria vota 1-5 su sei criteri a pari peso: idea, prototipo, novita',
impatto sociale, gruppo, presentazione (dettaglio in
`docs/materiali/README.md`). Il prototipo e' solo uno dei sei: ogni ora di
codice va giustificata anche rispetto a pitch, impatto e novita'.

### Ordine di priorita'

Quando due obiettivi sono in conflitto: **demo che gira -> correttezza di cio'
che la demo mostra -> chiarezza della storia -> aspetto visivo -> qualita' del
codice.**

## Economia del progetto

Vincolo permanente, valido per ogni agente e ogni sessione.

- Velocita' e basso consumo di token prima di completezza ed eleganza.
- Niente unit test estesi, niente hardening, niente astrazioni difensive,
  niente funzionalita' anticipate, niente refactor non richiesti.
- Piani e specifiche brevi: obiettivo, file toccati, task, verifica. Nessuna
  sezione decorativa.
- Ogni consegna porta **un solo controllo eseguibile** (comando, script, pagina
  aperta nel browser) con il suo output. Niente "dovrebbe funzionare". Se
  qualcosa fallisce o e' stato saltato, lo si dice.
- Si legge solo cio' che serve al task: niente esplorazioni dell'intero repo.
  Nei documenti lunghi si cerca la sezione (`grep -n`) e si leggono solo quelle
  righe (`sed -n 'A,Bp'`).
- Linter e formattazione: una passata alla fine, non durante il lavoro.
- Analisi con tre opzioni solo per scelte rilevanti o irreversibili (challenge,
  stack, formato dati); il resto si decide e si procede.

## Implementazione: subagent driven development snello

- `superpowers:subagent-driven-development` in modalita' minimale.
- Un implementer alla volta, sequenziale, nello stesso working tree.
- Implementer su modello medio (Sonnet o equivalente) quando il task e' chiaro e
  circoscritto; il controller resta sul modello della sessione.
- **Nessun reviewer agent, nessun ciclo di re-review.**
- Un solo controllo finale del controller su diff e verifica eseguibile; i
  problemi trovati si correggono direttamente.
- Il controller passa all'implementer solo il task corrente e i contratti
  necessari, non l'intero contesto.
- Brainstorming e piano solo per lavori di piu' di un'ora; per il resto si
  implementa direttamente.
- **Classificare prima di correggere:** davanti a un comportamento inatteso,
  capire a quale componente appartiene e correggere li', mai a valle.
- **Frontend:** aprire il browser e guardare, su desktop e a larghezza
  telefono, prima di dichiarare finita una schermata.

Agenti senza subagent (es. Codex): stesso flusso, eseguendo i task del piano in
sequenza e verificando ognuno.

## Lavoro in team

- **Un branch per persona o feature** (`nome/feature`), merge frequenti su
  `main`: piccoli e spesso, mai a fine giornata.
- `main` deve sempre avviarsi. Chi rompe `main` lo ripara per primo.
- Due persone sullo stesso modulo si accordano prima, non dopo.
- I contratti tra componenti (API, formato dati, schema) si fissano in
  `docs/specifiche/` **prima** di lavorare in parallelo e si cambiano solo
  avvisando il team.
- In `STATO.md` ognuno modifica solo la propria riga della tabella "Chi fa
  cosa": riduce i conflitti di merge.
- Segreti e chiavi API solo in `.env` (ignorato da Git); i nomi delle variabili
  in `.env.example`.

## Struttura

```text
AGENTS.md          come si lavora qui (CLAUDE.md e GEMINI.md lo importano)
STATO.md           dove siamo adesso: volatile, si riscrive a ogni sessione
README.md          avvio e comandi, per le persone
ONBOARDING.md      guida per i nuovi del team e i loro agenti, problemi frequenti
.githooks/         hook versionati, vedi "Attivazione degli hook"
docs/              memoria del progetto, tabella sotto
```

```text
infra/             compose.yaml (PostGIS, progetto Docker "sentinelle") + schema.sql
dati/              GeoJSON CFVA, pericolo AIB, comuni (ignorati da Git) + offline/
scripts/           setup.sh (primo avvio), avvia.sh, backend.sh, python.sh,
                   pubblica_dati.sh (dump -> release "dati-v1"), scarica_dati,
                   carica_dati, semina_demo, reset_demo.sql, prova_*, genera_tiles, tunnel.sh
backend/           FastAPI (src/sentinelle: fonti/ FIRMS meteo Corine, api/, rischio,
                   verifica = priorita', gioco, eventi = SSE), config/*.toml, tests/
frontend/          Nuxt 4: pages/app.vue (cittadino), pages/cruscotto.vue (operatori),
                   public/tiles/*.pmtiles (mappa base offline e storico)
```

Avvio e comandi in `README.md`; `.claude/launch.json` ha `backend` e `frontend`.

### Dove si scrive cosa

Ogni cartella risponde a una domanda. Se un contenuto non risponde a nessuna,
appartiene a `STATO.md` o a un commento nel codice.

| Percorso | Domanda | Ciclo di vita |
|---|---|---|
| `docs/materiali/` | Cosa ci hanno dato gli organizzatori? | Sola lettura, piu' il README di sintesi |
| `docs/dominio/` | Com'e' fatta la realta' degli incendi? Indici, dati, normative, attori | Autorita' esterna: la registriamo, non la decidiamo |
| `docs/decisioni/` | Perche' abbiamo scelto cosi'? | Append-only: una decisione superata si annota come superata, non si riscrive |
| `docs/interfaccia/` | Come si vede? Linguaggio visivo, token, widget | Corrente, si aggiorna in place: leggerlo prima di toccare il frontend |
| `docs/specifiche/` | Cosa deve fare questa parte, e con quali contratti? | Una per componente, prima del piano |
| `docs/piani/` | Con quali passi la costruiamo? | Documento vivo durante l'esecuzione |
| `docs/esperimenti/` | Cosa abbiamo misurato su dati o modelli? | Configurazione, comando, risultato |
| `docs/pitch/` | Cosa raccontiamo alla giuria? | Storia, slide, script della demo, domande attese |
| `docs/debito.md` | Cosa abbiamo tagliato di proposito? | Diventa la slide "sviluppi futuri" |

File datati con prefisso `AAAA-MM-GG-slug.md` (anche le decisioni: evita
collisioni di numerazione tra branch). **Se una skill di pianificazione propone
un percorso diverso (`docs/superpowers/` o simili), usa comunque queste
cartelle.**

**Un piano in esecuzione e' un documento vivo.** Si spuntano le checkbox
`- [x]` man mano: e' cio' che permette a un altro agente o a un compagno di
riprendere senza rileggere il codice. Se un task cambia forma, si annota la
deviazione nel piano invece di eseguirla in silenzio.

## Consegna e ripresa

La memoria del progetto vive **nel repository**, non nelle memorie private dei
singoli agenti: cosi' e' condivisa da tutto il team e da ogni strumento. Le
memorie private servono solo per preferenze personali. Nulla di vincolante
resta solo in chat.

### Parole chiave

- **«riprendi»**: leggere stato, verificare commit successivi al riferimento,
  leggere il piano attivo, riassumere da dove si riparte e il prossimo passo
  **senza modificare nulla**.
- **«consegna»**: aggiornare stato e piano, promuovere in `docs/decisioni/` le
  decisioni vere, eseguire la verifica proporzionata, proporre il commit.

### Alla fine di ogni sessione

Aggiorna `STATO.md` prima dell'ultimo commit con:

- il commit di riferimento (`git rev-parse --short HEAD`, quello **prima** del
  commit finale);
- la tua riga in "Chi fa cosa": task, branch, prossimo passo concreto;
- cosa e' stato deciso o scoperto **fuori** da un piano: e' la parte che si
  perde piu' facilmente;
- cosa resta aperto o da chiarire con il team.

Lo SHA, non la data: `git log <sha>..HEAD` mostra esattamente cosa non e'
riflesso nello stato, quindi un file obsoleto si autodenuncia invece di essere
creduto.

### Attivazione degli hook

`.git/hooks` non e' versionato. Lo attiva `scripts/setup.sh`; a mano, una volta per clone:

```bash
git config core.hooksPath .githooks
```

Il `pre-commit` **avvisa, non blocca**, quando un commit tocca il codice senza
aggiornare `STATO.md`. Gira a prescindere dall'agente, anche su commit a mano.

## Commit

- Una riga, breve, descrive solo cosa e' cambiato. Nessun co-autore, nessuna
  firma di agenti.
- Commit e push solo su richiesta di chi sta lavorando.
- Niente emoji nell'output salvo richiesta esplicita.
