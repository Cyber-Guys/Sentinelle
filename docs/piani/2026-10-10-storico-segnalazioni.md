# Storico delle segnalazioni

> Per agenti: SDD snello (AGENTS.md). Spuntare le checkbox, annotare le deviazioni.

**Stato:** completato

**Obiettivo:** le segnalazioni valutate (confermate e falsi allarmi) restano come
storico visibile sulla mappa, nel cruscotto e nell'app; il cittadino segue lo
stato delle proprie segnalazioni.

## Contratti

### Database
`ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS valutata_il timestamptz`
(schema.sql + DDL eseguito all'avvio). Valorizzata da conferma e archiviazione.
`reset_demo.sql` invariato (TRUNCATE).

### API
```text
GET /segnalazioni?stato=nuova|confermata|archiviata|valutate|tutte&utente_id=&limite=500
    -> [Segnalazione] ; nuova: priorita desc ; altrimenti valutata_il/creata_il desc
Segnalazione += valutata_il, punti_ottenuti (50 se fuoco confermata, 10 se area_a_rischio
                con punti assegnati all'invio, altrimenti 0)
```
Il contatore "confermate oggi" del cruscotto usa `valutata_il`.

### Stati e pin (stesso linguaggio dei pin pulsanti)
| Stato | Etichetta UI | Pin |
|---|---|---|
| nuova | In valutazione | colore priorita' (cruscotto) / ambra (app), onda |
| confermata | Confermata | pieno, colore priorita' (cruscotto) / macchia (app), fermo, bordo chiaro |
| archiviata | Falso allarme | anello grigio (`testo-3`) vuoto, fermo |

## Task

### Task 1: backend
- [x] Colonna, filtri, ordinamento, campi nuovi; conferma/archivia valorizzano `valutata_il`.
- **Verifica:** `scripts/prova_percorso.py` passa; curl su `stato=valutate` e `utente_id`.

### Task 2: cruscotto
- [x] Pannello Livelli: nuovo interruttore "Storico segnalazioni" con filtro Confermate / Falsi allarmi / Entrambe; pin fermi come da tabella; popup (PopupMappa) con stato, data valutazione, priorita' e azione "Apri scheda" che apre la scheda dettaglio in sola lettura (niente Conferma/Falso allarme, badge di stato).
- [x] "Confermate oggi" su `valutata_il`.

### Task 3: app cittadino
- [x] Quarta scheda "Segnalazioni" nella navigazione (Mappa, Missioni, Segnalazioni, Classifica; icona lucide adatta), verificata a 375 px.
- [x] Elenco delle proprie segnalazioni (`utente_id`): stato con colore+parola, data, comune, priorita', punti ottenuti; tocco -> torna alla Mappa e vola sul pin aprendo il popup. Stato vuoto curato.
- [x] Pin delle proprie segnalazioni sempre visibili sulla mappa (tabella stati).
- [x] Polling leggero (10 s) delle proprie segnalazioni: al cambio di stato toast "La tua segnalazione #N e' stata confermata · +50 punti" / "... archiviata come falso allarme", aggiornamento punti e livello.

### Task 4: consegna
- [x] `docs/interfaccia/linguaggio-visivo.md` (tabella pin con stati), STATO.md.

## Deviazioni

- Task 1: aggiunta colonna `punti_ottenuti int not null default 0` (non era memorizzato se i +10 erano stati assegnati); valorizzata all'invio (10 se entro il limite) e alla conferma di un fuoco (50).
- Task 2: il cruscotto non ha lo storico incendi, quindi i layer `storico-segn` stanno sopra le mappature e sotto la coda; un clic che colpisce anche un pin della coda va alla coda. Filtro a segmenti (Entrambe / Confermate / Falsi allarmi) dentro la sezione; storico caricato anche all'avvio perche' serve alla scheda in sola lettura.
- Task 3: navigazione a 4 voci con etichetta solo sulla voce attiva (le altre icone 44 px con `aria-label`): a 375 px quattro etichette non stanno. Pallino brace sulla voce Segnalazioni dopo una valutazione non vista. Toast esteso (`ToastPunti`: `nota` + `esito` ok/no) per le valutazioni senza punti; un popup aperto sulla segnalazione appena valutata si riapre col nuovo stato. Pin e popup condivisi: `aggiungiPinSegnalazioni()`/`geojsonSegnalazioni()` in `useMappa.ts`, `PopupSegnalazione.vue`, `STATI` in `useApi.ts`.
