# Waze per gli incendi (app cittadino)

**Data:** 2026-10-16
**Stato:** bozza in discussione (non ancora implementata). Nata dal confronto
con i mentor all'hackathon. Le scelte marcate *[proposta]* sono del controller
e vanno confermate o corrette; le altre sono decise da Alessandro.

## Problema e intento

Durante un incendio i centralini (1515, 112) si intasano: tante persone
chiamano per lo stesso fumo. L'app diventa **la mappa condivisa degli incendi
in tempo reale**, come Waze per il traffico: prima di chiamare vedi se quella
zona e' gia' segnalata, e invece di chiamare confermi. Il cittadino passa da
"chi chiama" a "sensore della comunita'".

Messaggio per il pitch: meno chiamate doppie, segnalazioni piu' affidabili,
operatori che ricevono un quadro gia' consolidato.

**Vincolo etico, sempre visibile:** l'app non sostituisce il numero di
emergenza. Testo fisso: "Se sei in pericolo o vedi fiamme vicino a persone o
case, chiama sempre il 112". L'app riduce le chiamate *ripetute*, non quelle
necessarie.

## Decisioni prese (Alessandro)

- **Visibilita':** tutte le segnalazioni attive sono visibili sulla mappa a chi
  guarda quella zona. Sotto soglia appaiono come "Da verificare" (pin tenue,
  senza alone, testo esplicito); sopra soglia con lo stato pieno.
- **Conferma solo sul posto:** si puo' confermare o dire "Non c'e' piu'" solo
  se il GPS e' entro il raggio della segnalazione (2 km); fuori raggio i
  pulsanti sono disattivati con il motivo ("Avvicinati entro 2 km per
  confermare").
- **Tipi nella demo:** Fuoco, Fumo, Area a rischio, Strada bloccata, Persone o
  animali in pericolo (tutti e cinque).
- **Chiusura:** possono chiuderla sia i cittadini ("Non c'e' piu'") sia
  l'operatore.
- **Privacy:** mai i nomi; solo conteggi ("8 cittadini hanno confermato").
- **Alert di prossimita':** chi si trova vicino a una zona segnalata riceve un
  avviso e puo' andare a confermare (o ignorare).
- **Peso dell'affidabilita' dell'utente:** lasciato al controller (sotto).

## 1. Segnalare in due tocchi

- Un solo pulsante "Segnala" -> griglia di tipi grandi con icona:
  Fuoco, Fumo, Area a rischio (sterpaglie/rifiuti), Strada bloccata,
  Persone o animali in pericolo. *[proposta]* niente sotto-domande obbligatorie.
- Posizione GPS automatica (correggibile toccando la mappa), foto facoltativa,
  invio immediato.
- **Anti-doppione:** se entro il raggio esiste gia' una segnalazione dello
  stesso tipo nella finestra di tempo, l'app propone "C'e' gia' una
  segnalazione di fumo a 300 m: e' la stessa?" -> "Si', confermo" (diventa una
  conferma) / "No, e' un altro punto" (nuova segnalazione).
  *[proposta]* raggio 500 m per fuoco/fumo, 200 m per gli altri tipi; finestra 3 h.
- Le missioni restano nella scheda Missioni; "Area a rischio" e' un tipo di
  segnalazione.

## 2. Mappa condivisa e stato ufficiale

- L'app si apre sulla mappa con le segnalazioni attive sopra soglia nella zona.
- Ogni segnalazione mostra: tipo, da quanto tempo, numero di conferme,
  affidabilita' in parola, **stato ufficiale** dal cruscotto:
  "In verifica" -> "Operatori allertati" -> "Mezzi sul posto" -> "Spento".
  *[proposta]* lo stato ufficiale e' cio' che fa davvero smettere di chiamare:
  il cruscotto deve poter impostare questi stati (oggi ha solo conferma/falso
  allarme).
- Toccandola: "C'e' ancora" / "Non c'e' piu'", foto degli altri (se presenti),
  conteggi, ultimo aggiornamento.

## 3. Conferme e chiusura

- Un voto per utente per segnalazione; non si conferma la propria.
- "C'e' ancora" aggiunge peso; "Non c'e' piu'" lo toglie.
- *[proposta]* Chiusura da parte dei cittadini: se il peso dei "Non c'e' piu'"
  supera quello delle conferme recenti (ultimi 30 min) la segnalazione passa a
  "Probabilmente spento" per tutti; resta in coda all'operatore, che la chiude
  definitivamente ("Spento") o la riapre. L'operatore puo' chiudere sempre.

## 4. Affidabilita' (scelte del controller, da validare)

**Affidabilita' dell'utente** r in [0,1], stile bayesiano sullo storico reale:
`r = (confermate + 1) / (valutate + 2)` contando le sue segnalazioni e conferme
poi confermate o smentite dagli operatori. Nuovo utente: 0,5. Visibile al
cittadino come livello ("Sentinella affidabile") insieme a quello di gioco.

**Punteggio di una segnalazione** (spiegabile, come la priorita' di oggi):

```text
punteggio = somma dei pesi delle conferme indipendenti (peso = r dell'utente, autore incluso)
          - somma dei pesi dei "Non c'e' piu'"
          + prove: hotspot satellitare entro 2 km (+1,5), foto (+0,3), cella a rischio alto (+0,3)
          con decadimento nel tempo: emivita 2 h per fuoco/fumo, 6 h per gli altri tipi
```

Soglie:
| Punteggio | Stato per i cittadini | Visibile a |
|---|---|---|
| < 1,0 | Da verificare | tutti (pin tenue); confermabile solo entro 2 km |
| >= 1,0 | Probabile | tutti |
| >= 2,5 | Confermata dalla comunita' | tutti |
| conferma operatore | Confermata dagli operatori | tutti |

Conseguenze: un utente molto affidabile con una foto vicino a un hotspot
supera subito la soglia; un utente nuovo da solo no, servono 1-2 conferme.
Punti di gioco (scelta del controller), assegnati solo all'esito
dell'operatore, cosi' i falsi allarmi non convengono:
| Azione | Punti | Quando |
|---|---|---|
| Prima segnalazione (fuoco/fumo) | +50 | confermata dall'operatore (come oggi) |
| Prima segnalazione (altri tipi) | +20 | confermata dall'operatore |
| Conferma "C'e' ancora" | +10 | se la segnalazione e' confermata dall'operatore |
| "Non c'e' piu'" corretto | +10 | se l'operatore la chiude come spenta |
| Voto smentito dall'operatore | 0 punti, l'affidabilita' cala | sempre |
Bonus "primo a confermare" +5. Le conferme migliorano anche l'affidabilita'
dell'utente, che vale piu' dei punti.

Anti-abuso minimo per la demo: un voto per utente, limite di segnalazioni per
ora, conferme che contano solo se il GPS e' entro 2 km dal punto.

## 5. Alert di prossimita'

- Quando l'utente e' entro ~2 km da una segnalazione attiva:
  - sopra soglia: avviso informativo ("Fumo segnalato a 1,2 km · 6 conferme ·
    Operatori allertati") con "C'e' ancora" / "Non c'e' piu'" / "Ignora";
  - sotto soglia: richiesta di verifica ("Qualcuno ha segnalato fumo vicino a
    te: lo vedi?").
- *[proposta]* Demo: avvisi con app aperta (GPS in primo piano, `watchPosition`)
  piu' notifiche Web Push quando l'app e' chiusa se c'e' tempo. Il geofencing
  in background vero richiede un'app nativa: dichiararlo come sviluppo futuro.
- Non insistere: un avviso per segnalazione per utente.

## 6. Impatti sul resto della piattaforma

- Cruscotto: la coda riceve segnalazioni gia' consolidate (con conteggi e
  punteggio); nuovi stati ufficiali; le conferme dei cittadini diventano un
  fattore della priorita'.
- Il punteggio di affidabilita' diventa un fattore in `ScomposizionePriorita`.
- Le segnalazioni esistenti (tabella `segnalazione`) si estendono con
  conferme/smentite in una tabella `voto_segnalazione` (utente, tipo voto,
  posizione, istante).

## Domande ancora aperte

1. Stati ufficiali del cruscotto: bastano i quattro proposti (In verifica,
   Operatori allertati, Mezzi sul posto, Spento)? In mancanza di risposta si
   usano questi.

Chiuse il 2026-10-16: visibilita' (tutti vedono, conferma solo entro 2 km),
cinque tipi nella demo, punti (tabella sopra).

## Fuori perimetro della demo

Geofencing in background, verifica identita' (SPID), integrazione reale con
NUE 112 / 1515: in `docs/debito.md` come sviluppi futuri.
