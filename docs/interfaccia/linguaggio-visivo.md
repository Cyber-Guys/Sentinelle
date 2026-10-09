# Linguaggio visivo

Riferimento di qualita': `cia-sardegna-learning` (`frontend/app/assets/css/tema.css`,
`docs/interfaccia/linguaggio-visivo.md`, componenti `RiquadroVetro`,
`AnelloLivello`, `WidgetTempo`, `Scudetto`). Da li' si prendono metodo e cura,
non i colori: CIA e' blu istituzionale, Sentinelle e' **la notte d'estate in
Sardegna con un fuoco all'orizzonte**.

## Principi

- **Scuro per primo.** Il tema scuro e' il default e quello curato di piu';
  il chiaro e' un'alternativa dignitosa, attivata da un interruttore.
- **Atmosfera sotto tutto.** Fondo quasi nero blu-notte; in basso un bagliore
  radiale brace (arancio-rosso, molto tenue) come un incendio lontano; in alto
  un accenno di verde macchia mediterranea. Grana finissima (~3%). Pseudo
  elementi `position: fixed` su `body`, fondo su `html` (trappola di CIA).
- **Vetro, non riquadri piatti.** Superfici traslucide con `backdrop-filter`,
  bordo di luce sottile in alto. Quattro livelli come CIA: atmosfera, `barra`,
  `vetro`, `sospeso`. Niente quinto livello.
- **Elementi che fluttuano.** Navigazione a pillola sospesa in basso (non una
  barra piena), controlli della mappa come pillole di vetro sopra la mappa.
- **Mappa protagonista e a tutto schermo** nell'app; i pannelli scorrono sopra
  come fogli di vetro. Mappa base vettoriale **Protomaps offline** (tile, font e
  sprite serviti da `public/`, nessuna rete): flavor `dark` ritoccato sui token
  nel tema scuro, `light` nel chiaro, etichette in italiano, attribuzione visibile.
- **Un solo accento pieno per schermata**, sull'azione principale (Segnala):
  gradiente brace. Il resto in tinte tenui.
- **Cifre come contenuto.** Punti, priorita', ettari in caratteri grandi,
  `tabular-nums`. Stati sempre colore + parola/icona, mai colore da solo.
- **Movimento sobrio.** Transizioni 150-250 ms, numeri che contano verso il
  valore nuovo, pulsazione lenta sui marker di fuoco. Tutto spento con
  `prefers-reduced-motion`.
- **Icone** solo `@lucide/vue`.

## Token

| Ruolo | Scuro | Chiaro |
|---|---|---|
| fondo | `#07090d` | `#f6f4ef` |
| testo / 2 / 3 | `#f3f1ec` / `#a7a39a` / `#6f6b63` | `#1a1a17` / `#5b5850` / `#8b877d` |
| vetro / forte | `rgba(255,255,255,.045)` / `.075` | `rgba(255,255,255,.62)` / `.82` |
| bordo / luce | `rgba(255,255,255,.08)` / `.16` | `rgba(20,20,10,.08)` / `.14` |
| brace (accento) | `#ff6a2b` -> `#e8351f` | idem |
| ambra | `#f5b83d` | `#d99a1e` |
| macchia (verde) | `#3fb37f` | `#2f8f63` |
| cielo (info) | `#5aa9e6` | `#2f7fc0` |

Scala della priorita' (anche per il rischio): bassa `macchia`, media `ambra`,
alta `brace`, sempre con l'etichetta. Incendi storici: da ambra tenue (vecchi)
a brace (recenti).

Raggi: 10 / 14 / 20 px, pillole 999 px. Font di sistema (SF Pro su Apple).

## Interruttore del tema

Attributo `data-tema="scuro|chiaro"` su `html`, token come variabili CSS
ridefinite per tema. Default scuro; scelta salvata in `localStorage` (con
try/catch). Interruttore a pillola con icona luna/sole, presente in app e
cruscotto. Lo stile della mappa base cambia insieme al tema.

## Widget di riferimento

- **Anello del livello** (come `AnelloLivello` di CIA): anello di avanzamento
  verso il prossimo livello attorno alle iniziali dell'utente.
- **Indicatore del rischio di oggi**: arco/gauge con valore, livello in parola
  e le grandezze meteo che lo determinano (vento, umidita', giorni senza
  pioggia), come `WidgetTempo` di CIA.
- **Scheda segnalazione**: priorita' come numero grande dentro un anello
  colorato, motivazioni come righe con icona.

## Emerso in implementazione

- **Token in `frontend/app/assets/css/tema.css`**: variabili su `html[data-tema]`,
  esposte a Tailwind con `@theme inline` (`bg-vetro`, `text-brace`, `bg-brace/12`...).
  Il tema si applica con uno script inline in `<head>` (`nuxt.config`, `SCRIPT_TEMA`
  in `useTema.ts`): niente lampo al caricamento.
- **Nel chiaro le tinte usate come testo scendono di luminosita'** (brace `#d9481a`,
  ambra `#b07510`, macchia `#2b8259`) per restare leggibili su `#f6f4ef`; i layer
  della mappa usano i valori della tabella (`coloriMappa` in `useMappa.ts`).
- **Sopra la mappa il vetro e' piu' denso** (`--vetro-mappa`, ~75%): con il vetro
  al 4,5% le etichette della carta si leggono attraverso le pillole.
- **Il contenitore della mappa va avvolto**: MapLibre mette `position: relative`
  sul nodo della mappa e annulla un `absolute inset-0` scritto li'.
- **Layer della mappa in una funzione su `style.load`**: al cambio tema
  `setStyle(..., { diff: false })` cancella sorgenti e layer, che si ri-aggiungono
  dagli ultimi dati in memoria; i listener per id di layer restano validi.
- Stile Protomaps generato in `stileMappa()` (`@protomaps/basemaps`, `lang: 'it'`) con i colori del flavor ritoccati (fondo, terra, acqua, strade) per avvicinarli ai token. Sorgente `pmtiles:///tiles/sardegna.pmtiles` (bbox Sardegna, zoom 14; oltre viene ingrandito), glyphs e sprite con URL assoluto sull'origine corrente. Va chiamato `registraPmtiles()` in ogni pagina con mappa.
- L'attribuzione OSM + Protomaps arriva dalla sorgente dello stile: controllo compatto ("i").
- **Tre stati per ogni dato remoto: caricamento, errore, vuoto.** Caricamento = `scheletro`
  (utility in `tema.css`) con la forma del contenuto in arrivo, mai uno spinner al posto di
  un elenco; i titoli restano veri, solo i dati sono scheletri. Errore = `StatoErrore` (vetro,
  frase non tecnica da `messaggioErrore()` in `useApi.ts`, un solo pulsante "Riprova"); mai
  `e.message` a schermo. Vuoto = icona in cerchio tenue + frase che dice cosa succedera'
  ("Tutto tranquillo", "La sfida e' appena iniziata"), non solo "nessun dato". Una classifica
  con righe tutte a zero punti conta come vuota.
- **Polling che fallisce non svuota lo schermo**: si tengono gli ultimi dati e si segnala
  "Connessione persa · riprovo da solo" nella pillola di stato (cruscotto).
- **Movimento**: numeri con `useConteggio()` (~600 ms, easing in uscita); pressione = `scale`
  0.98 globale (proprieta' `scale`, non `transform`, per non rompere `-translate-x-1/2`);
  fogli in entrata 320 ms `cubic-bezier(.22,1,.36,1)` e in uscita 140 ms, cosi' due fogli
  che si scambiano non restano sovrapposti; nuove righe della coda entrano scivolando e
  restano bordate di brace ~4 s. Con reduced-motion: niente scala, scheletri fermi.
- **Un evento, un messaggio**: col salto di livello il riquadro "Nuovo livello" porta anche i
  punti e il toast non compare (prima si sovrapponevano). Il riquadro si chiude toccandolo.
- **Tocco >= 44 px** nell'app: utility `tocco` (area invisibile allargata) sui pulsanti
  disegnati piu' piccoli; controlli MapLibre a 40 px nell'app; testi dei controlli in italiano
  con `LOCALE_MAPPA`.
- **Contrasto nel chiaro**: `testo-3` `#6d6960`, brace `#c43f14`, ambra `#956207`, macchia
  `#277752` (>= 4,5:1 su `#f6f4ef`); nello scuro `testo-3` `#8a867e`.
- **Glifi della mappa**: in `public/basemap/fonts` ci sono solo gli intervalli latini; la rotta
  `server/routes/basemap/fonts/[...intervallo].ts` risponde pbf vuoto agli altri (arabo e
  tifinagh delle etichette nordafricane a zoom 6), altrimenti console piena di avvisi.
- Mappa scura: terra `#11151c`, mare `#0a1729` (blu-notte), verde appena piu' chiaro della terra.
