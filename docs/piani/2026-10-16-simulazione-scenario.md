# Simulazione di scenario e rischio di oggi

> Per agenti: SDD snello (AGENTS.md). Spuntare le checkbox, annotare le deviazioni.

**Stato:** chiuso
**Specifica:** `docs/specifiche/2026-10-16-simulazione-scenario.md` (contratti li').

## Task

### Task 1: backend rischio di oggi
- [x] Tabella `cella` + `scripts/prepara_celle.py` (idempotente, eseguito anche da `setup.sh` se la tabella e' vuota), meteo a griglia con cache, `GET /rischio/griglia`.
- **Verifica:** conteggio celle, tempo di risposta, distribuzione valori (min/mediana/max).

### Task 2: backend simulazione
- [x] `backend/src/sentinelle/simulazione.py` (motore puro: griglia, Dijkstra con meteo orario) + `POST /simulazione`; test mirato sul motore (vento da ovest -> area allungata a est; mare non brucia).
- **Verifica:** simulazione 24 h da un hotspot reale: tempo, ettari per ora, comuni raggiunti.

### Task 3: frontend
- [x] Pannello scenario nel cruscotto (orizzonte, cursore, play, statistiche, nota), layer aree/fronte/origine, avvio da popup hotspot, scheda segnalazione e clic destro; livello "Rischio di oggi" nei Livelli. Mobile: pannello nel foglio.
- **Verifica:** browser desktop e telefono, scuro e chiaro; scenario 24 h giocato fino in fondo.

### Task 4: consegna
- [x] `linguaggio-visivo.md`, README (prepara_celle), STATO.md.

## Deviazioni

- `prepara_celle.py` impiega ~11 min (intersezione pericolo AIB per area): una tantum, da setup.sh solo se `cella` e' vuota. Celle: 5494.
- Meteo orario in `fonti/meteo_orario.py` (70 punti 0,25 gradi, una chiamata, cache 1 h, `past_days=14` per i giorni senza pioggia). Rete giu': maestrale costante 25 km/h da 300, `note` lo dichiara; dopo un fallimento non si riprova per 5 min. `GET /rischio/griglia` aggiunge `meteo_simulato`; `POST /simulazione` aggiunge `durata_s`.
- Taratura (`[simulazione]` in pesi.toml, base 2,5 m/min, k_vento 0,06), combustibile pieno: vento 30 km/h -> ~44 ha 1 h, ~1500 ha 6 h, ~23000 ha 24 h; vento 5 km/h -> ~1800 ha 24 h. Il primo passo e' sottostimato dalla griglia 200 m.
- Acqua: solo mappature `punto_acqua` (nome generico "Punto d'acqua segnalato").
- Frontend: `PannelloScenario.vue` (desktop `sospeso` al posto della scheda, telefono nel foglio), `LivelloRischio.vue` (app e cruscotto); layer in `useMappa.ts` (`aggiungiScenario`, `impostaOraScenario`, `rimuoviScenario`, `aggiungiRischio`). Durante lo scenario lo storico incendi si nasconde (stessi colori caldi). Le aree orarie sono cumulative: opacita' delle ore passate divisa tra loro (nucleo piu' denso, max ~55% a 24 h). Pressione lunga 600 ms gestita a mano (iOS non emette `contextmenu`). `.interruttore` spostato in `tema.css` (serve anche all'app). In dev `window.__mappa` espone la mappa del cruscotto per le verifiche.
