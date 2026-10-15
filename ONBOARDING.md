# Onboarding

Guida operativa per chi entra nel team (e per il suo agente: Claude Code,
Codex, Gemini, Cursor). Le regole complete sono in `AGENTS.md`.

## 1. Prerequisiti

| Strumento | Perche' | Installazione |
|---|---|---|
| git | repo | macOS: `xcode-select --install`; Linux: `sudo apt install git` |
| Docker | database PostGIS | macOS: Docker Desktop; Linux: Docker Engine + plugin compose |
| Node >= 20 | frontend Nuxt | https://nodejs.org, `brew install node@22` o `nvm install 22` |
| Python 3.12 | backend | conda se lo usi gia', altrimenti uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| gh (GitHub CLI) | scaricare i dati demo | `brew install gh` / `sudo apt install gh`, poi `gh auth login` |
| cloudflared, qrencode | solo per la prova da telefono | `brew install cloudflared qrencode` |

`./scripts/setup.sh` controlla tutto e stampa cosa manca.

## 2. Accesso al repo

Il repo `ale24cocco/hackaton-incendi` e' privato: Alessandro deve aggiungerti
come collaboratore (GitHub -> Settings -> Collaborators). Accetta l'invito,
poi `gh auth login` (serve anche per scaricare i dati).

## 3. Setup e avvio

```bash
git clone https://github.com/ale24cocco/hackaton-incendi.git
cd hackaton-incendi
./scripts/setup.sh      # una volta, ~2 minuti; si puo' rilanciare quando si vuole
./scripts/avvia.sh      # ogni volta; Ctrl+C ferma tutto
```

`setup.sh` deve chiudersi con `Pronto.` e i conteggi 377 comuni / 27544
incendi. Poi: http://localhost:3000/app (cittadino) e
http://localhost:3000/cruscotto (operatori).

Con Claude Code: chiedi all'agente di avviare `backend` e `frontend` da
`.claude/launch.json`. Comandi Python sempre con `./scripts/python.sh`.

## 4. Le memorie del progetto

La memoria vive nel repository, non nella chat ne' nelle memorie private
dell'agente: cosi' chiunque (persona o agente) riprende da dove si era rimasti.

- **`STATO.md`**: dove siamo. Si legge a inizio sessione; il commit di
  riferimento in testa dice cosa e' successo dopo
  (`git log --oneline <sha>..HEAD`).
- **«riprendi»**: detto all'agente, legge stato, commit recenti e piano attivo
  e riassume il prossimo passo senza toccare nulla.
- **«consegna»**: detto all'agente a fine lavoro, aggiorna `STATO.md` e il
  piano, registra le decisioni e propone il commit.
- **Riga personale**: in `STATO.md`, tabella "Chi fa cosa", ognuno modifica
  solo la propria riga (branch, task, prossimo passo). Evita conflitti.
- **Dove si scrive cosa** (tabella completa in `AGENTS.md`): decisioni in
  `docs/decisioni/`, contratti tra componenti in `docs/specifiche/`, piani in
  `docs/piani/`, misure in `docs/esperimenti/`, pitch in `docs/pitch/`, tagli
  voluti in `docs/debito.md`.
- **Hook pre-commit** (attivato da setup): avvisa se committi codice senza
  aggiornare `STATO.md`. Non blocca.

## 5. Lavoro in team

- Un branch per persona o feature: `nome/feature` (es. `nicola/pitch`).
- Merge piccoli e frequenti su `main`; `main` deve sempre avviarsi.
- Prima di lavorare in parallelo sullo stesso confine (API, formato dati),
  fissate il contratto in `docs/specifiche/`.
- Un agente alla volta per cartella: per due agenti in parallelo serve un
  `git worktree` separato.
- Commit su una riga, senza firme di agenti.

## 6. Prova da telefono

Con l'app avviata: `./scripts/tunnel.sh` in un altro terminale. Inquadra il QR
code: si apre `/app` in HTTPS (serve per GPS e fotocamera).

## 7. Problemi frequenti

| Sintomo | Causa | Soluzione |
|---|---|---|
| `Bind for 0.0.0.0:5432 failed` / porta occupata | un altro Postgres (locale o vecchio container) | fermarlo (`docker ps`, `docker stop <nome>`; `brew services stop postgresql`) oppure `SENTINELLE_PORTA_DB=5433 ./scripts/setup.sh` (scrive la porta in `.env`) |
| Backend: `connection refused` all'avvio | il DB non era ancora pronto | usare `./scripts/avvia.sh`, che attende il DB; oppure `docker compose -f infra/compose.yaml up -d --wait` e riavviare il backend |
| `Cannot connect to the Docker daemon` | Docker spento | aprire Docker Desktop (Linux: `sudo systemctl start docker`) e rilanciare |
| `Ambiente Python di Sentinelle non trovato` | setup non eseguito o fallito | `./scripts/setup.sh`; per forzare un tipo: `SENTINELLE_PYTHON=uv ./scripts/setup.sh` (o `conda`, `venv`) |
| conda e venv entrambi presenti | `python.sh` usa `backend/.venv` se esiste, altrimenti conda `sentinelle` | cancellare quello che non usi |
| `Nessuna fonte di dati disponibile` / conteggi sbagliati | gh non autenticato o senza accesso | `gh auth login` e rilanciare; oppure farsi passare `sentinelle.dump` e `./scripts/setup.sh --dump sentinelle.dump`; per ripartire da zero: `docker compose -f infra/compose.yaml down -v` |
| Mappa vuota o errori `/api` nel browser | backend spento | controllare http://localhost:8000/salute |
