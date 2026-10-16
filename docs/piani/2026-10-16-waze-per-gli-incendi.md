# Waze per gli incendi

> Per agenti: SDD snello (AGENTS.md). Spuntare le checkbox, annotare le deviazioni.

**Stato:** pronto, non iniziato
**Specifica:** `docs/specifiche/2026-10-16-waze-per-gli-incendi.md` (decisioni,
soglie, punti: leggerla prima).

**Obiettivo:** l'app cittadino diventa la mappa condivisa delle segnalazioni:
segnala in due tocchi, vedi quelle degli altri, conferma o chiudi sul posto,
affidabilita' calcolata, alert di prossimita'; il cruscotto riceve
segnalazioni consolidate e pubblica uno stato ufficiale.

## Contratti

### Database (DDL idempotente nella sezione `-- gioco:` di `infra/schema.sql`)

```sql
-- tipi: fuoco, fumo, area_a_rischio, strada_bloccata, persone_pericolo
ALTER TABLE segnalazione DROP CONSTRAINT IF EXISTS segnalazione_tipo_check;
ALTER TABLE segnalazione ADD CONSTRAINT segnalazione_tipo_check
  CHECK (tipo IN ('fuoco','fumo','area_a_rischio','strada_bloccata','persone_pericolo'));
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS stato_ufficiale text NOT NULL DEFAULT 'in_verifica'
  CHECK (stato_ufficiale IN ('in_verifica','allertati','mezzi_sul_posto','spento'));
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS aggiornata_il timestamptz NOT NULL DEFAULT now();
CREATE TABLE IF NOT EXISTS voto_segnalazione (
  id serial PRIMARY KEY, segnalazione_id int NOT NULL REFERENCES segnalazione ON DELETE CASCADE,
  utente_id int NOT NULL REFERENCES utente, voto text NOT NULL CHECK (voto IN ('ancora','finito')),
  geom geometry(Point,4326) NOT NULL, creato_il timestamptz NOT NULL DEFAULT now(),
  UNIQUE (segnalazione_id, utente_id));
```
`stato` attuale (nuova/confermata/archiviata) resta l'esito operatore;
`stato_ufficiale` e' cio' che vedono i cittadini. `reset_demo.sql` svuota anche
`voto_segnalazione`. Il trigger NOTIFY esistente si estende ai voti
(`segnalazione_aggiornata`).

### Logica (`backend/src/sentinelle/affidabilita.py`, funzioni pure + test)

```python
def affidabilita_utente(confermate: int, valutate: int) -> float      # (c+1)/(v+2)
def punteggio(voti: list[Voto], prove: Prove, eta_min: float, tipo: str) -> Punteggio
# Punteggio = {valore, livello: da_verificare|probabile|comunita|operatori, fattori: [...]}
```
Pesi, emivite (2 h fuoco/fumo, 6 h altri), soglie (1,0 / 2,5), bonus prove
(hotspot entro 2 km +1,5, foto +0,3, cella rischio alto +0,3), raggi
(conferma 2 km; doppione 500 m fuoco/fumo, 200 m altri; finestra 3 h) in
`backend/config/pesi.toml` sezione `[affidabilita]`.
"Probabilmente spento": peso "finito" degli ultimi 30 min > peso "ancora".

### API

```text
GET  /segnalazioni/attive?bbox=&utente_id=   -> [SegnalazioneCondivisa] (tutte le attive nel riquadro,
                                                 senza nomi; non spente da > 1 h)
SegnalazioneCondivisa = {id, tipo, lat, lon, creata_il, aggiornata_il, stato_ufficiale,
                         affidabilita: {valore, livello, fattori}, conferme, smentite,
                         probabilmente_spento: bool, foto_url?, mia: bool, mio_voto: 'ancora'|'finito'|null}
GET  /segnalazioni/vicine?lat=&lon=&tipo=    -> possibile doppione (entro raggio e finestra) o null
POST /segnalazioni/{id}/voto  form: utente_id, voto, lat, lon
                              -> SegnalazioneCondivisa; 422 se fuori 2 km, 409 voto gia' dato,
                                 403 propria segnalazione
POST /segnalazioni/{id}/stato json: {stato_ufficiale}   (cruscotto)
```
Punti assegnati all'esito operatore (tabella nella specifica): conferma dell'operatore
-> +10 a chi ha votato "ancora", +5 al primo; chiusura come spento -> +10 a chi ha votato
"finito"; prima segnalazione +50 fuoco/fumo, +20 altri tipi. Affidabilita' utente
ricalcolata dagli esiti.

## Task

### Task 1: backend dati e affidabilita'
- [ ] DDL, `affidabilita.py` con test (soglie, decadimento, voto pesato, probabilmente spento), pesi in configurazione.
- **Verifica:** pytest; calcolo su un caso costruito (1 utente nuovo = da verificare; + hotspot = probabile; 3 conferme = comunita').

### Task 2: backend API, punti, eventi
- [ ] Endpoint del contratto, anti-doppione, controllo raggio, punti all'esito, NOTIFY sui voti e sullo stato ufficiale, `prova_waze.py` (scenario: segnalazione, doppione proposto, 2 conferme da utenti vicini, una smentita lontana rifiutata, conferma operatore -> punti).
- **Verifica:** `prova_waze.py` e `prova_percorso.py` verdi.

### Task 3: app cittadino
- [ ] Pulsante Segnala -> griglia dei 5 tipi (icone Lucide, colori), GPS automatico, foto facoltativa, invio; banner fisso "Se sei in pericolo chiama sempre il 112".
- [ ] Anti-doppione: dialogo "C'e' gia' una segnalazione di fumo a 300 m: e' la stessa?" -> conferma / nuova.
- [ ] Mappa condivisa: pin per tipo e livello (Da verificare tenue senza alone; Probabile/Comunita'/Operatori pieni con alone), aggiornata via SSE; popup con stato ufficiale, conteggi ("8 cittadini"), da quanto, affidabilita' in parola, "C'e' ancora" / "Non c'e' piu'" (disattivati fuori 2 km con motivo), foto.
- [ ] Alert di prossimita' con app aperta (`watchPosition`): entro 2 km da una segnalazione attiva, avviso informativo o richiesta di verifica; una volta per segnalazione.
- [ ] Le proprie segnalazioni (scheda Segnalazioni) mostrano anche conferme e stato ufficiale.
- **Verifica:** browser desktop (posizione simulata con override di geolocalizzazione) e telefono vero via tunnel.

### Task 4: cruscotto
- [ ] Coda con conteggi, affidabilita' come fattore in `ScomposizionePriorita`, filtro per tipo; selettore dello stato ufficiale nella scheda (In verifica / Operatori allertati / Mezzi sul posto / Spento); "Probabilmente spento" evidenziato; i 5 tipi con le loro icone.
- **Verifica:** dal cruscotto lo stato ufficiale cambia sull'app in < 1 s.

### Task 5: consegna
- [ ] `linguaggio-visivo.md` (tipi, livelli di affidabilita', stati ufficiali), `docs/debito.md` (geofencing in background, SPID, integrazione NUE 112), STATO.md, ripubblicare il dump se cambia lo schema (`scripts/pubblica_dati.sh`).

## Deviazioni

Nessuna per ora.
