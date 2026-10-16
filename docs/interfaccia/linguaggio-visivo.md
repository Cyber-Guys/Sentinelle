# Linguaggio visivo

Riferimento di qualita': `cia-sardegna-learning` (`frontend/app/assets/css/tema.css`,
`docs/interfaccia/linguaggio-visivo.md`, componenti `RiquadroVetro`,
`AnelloLivello`, `WidgetTempo`, `Scudetto`). Da li' si prendono metodo e cura,
non i colori: CIA e' blu istituzionale, Sentinelle e' **la notte d'estate in
Sardegna con un fuoco all'orizzonte**.

## Principi

- **Professionale, non giocattolo.** Strumento operativo (riferimenti: Linear, Vercel, Waze
  notte): forme tondeggianti con raggi concentrici (vedi "Raggi"), bagliori solo dove servono (niente aloni
  attorno a loghi e pulsanti), pesi tipografici asciutti (titoli 600, cifre grandi 600), densita'
  da strumento, controlli alti 32-44 px. Header e controlli hanno larghezza intrinseca; fogli e
  pannelli hanno larghezza massima (440-480 px) e crescono col contenuto.
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
  valore nuovo, pin pulsanti sulla mappa (vedi "Pin pulsanti"). Tutto spento con
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

Font di sistema (SF Pro su Apple).

## Raggi concentrici

Token in `tema.css` (`@theme`, utility Tailwind `rounded-l|m|s`):

| Token | Valore | Dove |
|---|---|---|
| `--radius-l` | 22 px | contenitori: fogli `sospeso`, riquadri `vetro`, coda e scheda del cruscotto, card della home, popup della mappa |
| `--radius-m` | 10 px | elementi dentro un contenitore: righe, campi, tessere, vetro annidato, foto |
| `--radius-s` | 6 px | secondo livello: icone in riquadro dentro una tessera, scheletri |
| `--radius-ctrl` / `--radius-pill` | 999 px | pillole: navigazione, pulsante livelli, header utente, rischio, tema, legenda e controlli mappa, Segnala, pulsanti `primario` e `secondario`, badge |

- **Regola:** raggio interno = raggio del contenitore - padding che li separa. Per questo fogli
  e coda hanno padding 12 px (22 - 12 = 10 = `--radius-m`). Se il risultato scende sotto 6 si usa 6.
- **Vetro annidato:** `:where(.sospeso, .vetro) .vetro` prende da solo `--radius-m` (tessere
  delle missioni, righe della classifica, `StatoErrore` nella coda).
- **Pillole dentro pillole:** stessa regola (bottoni interni `rounded-full`); il campo posizione del foglio e' una pillola col pulsante GPS dentro.
- Azioni = pillole; superfici (tessere, campi, righe) = concentriche. Niente raggi scritti a mano
  nei componenti, salvo i loghi (`rounded-[32%]`, squircle che scala con la misura).

## Pin pulsanti

Linguaggio comune dei punti sulla mappa: punto pieno con bordo scuro (chiaro nel tema chiaro) +
alone che si muove. Colore per significato, sempre accompagnato da testo altrove (coda, legenda, foglio).

| Dove | Colore | Movimento |
|---|---|---|
| Segnalazioni nuove (cruscotto) | priorita': `macchia` / `ambra` / `brace` | onda che si allarga e svanisce, 2,6 s |
| Segnalazione selezionata (cruscotto) | colore della priorita' | in piu' un anello (solo bordo) piu' rapido, 1,6 s; punto piu' grande con bordo chiaro |
| Hotspot satellitari (app e cruscotto) | `brace` | respiro lento (cresce e cala), 3,8 s; punto piccolo |
| Punto scelto nell'app | fuoco `brace`, area a rischio `ambra`, missione `posizione` `macchia` | onda 2,6 s |
| Storico segnalazioni (cruscotto): confermata | colore della priorita', bordo chiaro (`testo`) | fermo |
| Storico segnalazioni (cruscotto): falso allarme | anello `testo-3` vuoto | fermo |
| Proprie segnalazioni (app): in valutazione | `ambra` | onda 2,6 s |
| Proprie segnalazioni (app): confermata | `macchia`, bordo chiaro | fermo |
| Proprie segnalazioni (app): falso allarme | anello `testo-3` vuoto | fermo |
| Posizione dell'utente ("tu sei qui") | `cielo` (`.pin-cielo`) | onda; oggi non mostrata: il GPS imposta il punto scelto |

- **Layer MapLibre** (coda, hotspot): `animaAloni()` in `useMappa.ts`, un solo
  `requestAnimationFrame` per mappa che aggiorna raggio/opacita' dei layer di alone: il costo non
  cresce col numero di pin. Nell'app parte solo se ci sono hotspot (niente ridisegno a vuoto).
- **Marker HTML** (punto scelto): classe `.pin` (+ `.pin-ambra|macchia|cielo`) in `tema.css`, onda
  in CSS (`scale` + `opacity`, solo compositor).
- **Stati delle segnalazioni** (`STATI` in `useApi.ts`, sempre colore + parola): nuova = "In valutazione" ambra, confermata = "Confermata" macchia, archiviata = "Falso allarme" `testo-3`. Layer con `aggiungiPinSegnalazioni()` (alone solo per le nuove, da animare con `aloneSegnalazioni()`), popup `PopupSegnalazione.vue` (stato, data, priorita', punti; nel cruscotto "Apri scheda" in sola lettura con badge e data di valutazione al posto delle azioni).
- **Segnaposto a icona (mappature dei cittadini, cruscotto):** discreti, in tema, fermi. Badge tondo
  di vetro (`fondo-3` al 92% nello scuro, bianco al 94% nel chiaro), anello 1,5 px e icona Lucide nel
  colore del tipo, punta minima di 4 px sul punto (`icon-anchor: bottom`), ombra appena accennata.
  Colori un tono sotto i token (`toniMappature()` in `useMappa.ts`): `punto_acqua` Droplet cielo,
  `sterpaglie` Leaf ambra, `rifiuti_strada` Trash2 viola, sconosciuto MapPin grigio. Disegnati su
  canvas a runtime (`registraSegnaposti()`, pixelRatio >= 2, ri-registrati a ogni `style.load`,
  `segnapostiMancanti()` su `styleimagemissing`); diametro ~17 px a zoom 6, 24 px da zoom 11.
  **Cluster** fino a zoom 11 (raggio 40): cerchio di vetro con anello tenue e numero `testo-2`, cresce
  poco col conteggio; clic = zoom di espansione. Legenda nel pannello Livelli con lo stesso badge.
- **Invasi (risorse idriche):** stesso segnaposto con icona Waves in `cielo`, percentuale di riempimento sotto da zoom 8 (testo cielo con alone vetro); popup PopupMappa con barra di riempimento, volumi, data e fonte; nello scenario righe con icona Waves e barra sottile.
- **Reduced-motion:** niente animazione; i valori statici dei layer e la base di `.pin::before`
  sono un alone fisso, quindi il pin resta leggibile.

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
- **Scomposizione della priorita'** (`ScomposizionePriorita.vue`, app e cruscotto): cifra grande
  + livello in parola + scala sottile 0-100 con soglie 30/60; poi una riga per fattore (icona,
  etichetta, testo del valore, barra del contributo, punti a destra in cifre tabulari). Le barre
  hanno scala comune (100% = contributo massimo del fattore piu' pesante): traccia chiara = massimo
  del fattore, riempimento = punti apportati, colore per intensita' del valore. Fattori non
  disponibili in grigio con "n.d.". Dati da `fattori` della segnalazione (backend `verifica.py`);
  le segnalazioni vecchie senza fattori mostrano le motivazioni.

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
- **Pulsante livelli** (`PulsanteLivelli.vue`, app): pillola tonda 44 px con icona `Layers` in cima alla colonna dei controlli a destra (sopra lo zoom di `ControlliMappa`, larghi uguali), badge con il filtro attivo (`2025`, `5 anni`, `2015+`). Apre un pannello `sospeso` ancorato a sinistra (scala + opacita' 180 ms dall'angolo del pulsante): sezione "Incendi storici" con elenco a radio (righe `rounded-m`) e legenda ambra -> brace per anno. Resta aperto dopo la scelta (il cambio si vede subito), si chiude toccando fuori, con Esc o la X. Nascosto in modalita' "scegli punto" e con i fogli missioni/classifica. Altri livelli futuri: nuove sezioni nello stesso pannello. Generico: nel cruscotto riceve le sezioni via slot (`badge`, `descrizione`, `v-model:aperto`). Niente piu' barra dei filtri sotto l'header.
- **Controlli mappa nostri** (`ControlliMappa.vue`, app e cruscotto), niente controlli di MapLibre (`NavigationControl`/`AttributionControl` e override `.maplibregl-ctrl*` rimossi): gruppo zoom a pillola 44 px con icone Lucide `Plus`/`Minus` 18 px (attenuate e disabilitate ai limiti di zoom), poi cerchio di vetro 36 px con `Info` che apre a sinistra una pillola alta 36 con l'attribuzione obbligatoria "© OpenStreetMap · Protomaps" (link in nuova scheda). Colonna destra = un contenitore flex verticale largo 44 con `gap-[14px]`: Livelli -> zoom -> "i", centri allineati, nessun offset calcolato.
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
  disegnati piu' piccoli; controlli della mappa a 44 px ("i" 36 con `tocco`); testi di MapLibre
  (popup) in italiano con `LOCALE_MAPPA`.
- **Contrasto nel chiaro**: `testo-3` `#6d6960`, brace `#c43f14`, ambra `#956207`, macchia
  `#277752` (>= 4,5:1 su `#f6f4ef`); nello scuro `testo-3` `#8a867e`.
- **Glifi della mappa**: in `public/basemap/fonts` ci sono solo gli intervalli latini; la rotta
  `server/routes/basemap/fonts/[...intervallo].ts` risponde pbf vuoto agli altri (arabo e
  tifinagh delle etichette nordafricane a zoom 6), altrimenti console piena di avvisi.
- **Stile mappa (Waze notte)**: in `useMappa.ts` si sovrascrivono solo i colori del flavor Protomaps.
  Terra blu-ardesia `#1a2130`, mare blu-notte `#0a1426`, linea di costa `#2b4568` (layer `costa`
  aggiunto sopra l'acqua), strade in gerarchia (autostrade `#8f9cb6`, principali `#66728b`, minori
  `#2b3343`-`#323b4d`), etichette chiare con alone scuro, verde/urbano appena accennati. Lo storico
  (ambra -> brace) e' l'unico colore caldo sulla carta. Chiaro: terra `#f1efe9`, mare `#b4cfe6`,
  vegetazione desaturata.
- **Niente bande allo zoom out**: `background` dello stile = colore del mare; `limitaMappa()` imposta
  `maxBounds` (lat dentro l'estratto 38.77-41.33, lon 5.6-12.3 dove c'e' solo mare aperto) e uno
  zoom minimo ricalcolato a ogni resize perche' i limiti riempiano sempre la finestra (verificato a
  375x812, 1440x900, 2560x1440).
- **Cruscotto**: colonna destra e pannello Livelli come l'app (Livelli 44 -> +/- 44 -> "i" 36 centrata, 14 px tra i bordi, cima allineata a coda e scheda a 76 px); il pannello ha in cima la sezione "Incendi storici" (stesso storico PMTiles, filtro e popup dell'app; interruttore on/off, default acceso su 2025, radio e gradiente solo se acceso; sotto tutti i pin, vince il pin al tocco; voce con campione del gradiente nella legenda) poi sezioni a interruttore (Hotspot satellitari, Mappature dei cittadini con legenda dei tipi) e il badge conta i livelli attivi. Legenda separata dai comandi: in basso a sinistra solo una pillola informativa (priorita', piu' hotspot se acceso). La coda si ferma sopra la legenda; la scheda dettaglio sta a 14 px a sinistra della colonna e scorre a sinistra del pannello Livelli quando e' aperto.

## Scenario e rischio di oggi

- **Scenario di propagazione** (cruscotto, `PannelloScenario.vue`): avvio da "Simula scenario" (primario nel popup hotspot, riga di vetro con Flame in `CorpoScheda`), clic destro sulla mappa o pressione lunga 600 ms; la legenda in basso suggerisce "Clic destro: simula scenario". Pannello `sospeso` largo come la scheda e nello stesso posto (desktop), contenuto del foglio a meta' (telefono). Ordine: badge "Scenario" brace + titolo "Scenario da <comune o coordinate>"; orizzonte a controllo segmentato (1/3/6/12/24 h, default 6, cambiarlo rilancia); riquadro con play/pausa tondo primario (diventa "da capo" alla fine), ora grande "+6 h · 18:00", cursore con riempimento ambra -> brace e pollice bianco; tre tessere (area in ettari brace con conteggio, vento con `Navigation2` cielo ruotata verso dove soffia + "da nord-ovest", umidita' con "aria secca" ambra sotto 30%); comuni con ora di contatto (raggiunti al cursore: riga bordata brace, punto pieno); acqua piu' vicina (tocco -> flyTo); nota di onesta' sempre visibile, piu' la frase sul meteo simulato in ambra se il backend la dichiara.
- **Mappa dello scenario**: aree cumulative filtrate `ora <= cursore`, piu' recenti sotto (`fill-sort-key`): ora corrente brace 34%, passate ambra con opacita' divisa tra le ore (il nucleo bruciato da piu' tempo e' il piu' denso). Fronte corrente = linea brace 2,4 px + bagliore sfocato. Origine = punto brace con bordo `testo` e onda 2 s (`ALONE_SCENARIO`). Primo calcolo: `fitBounds` sull'area finale nello spazio libero; al cambio orizzonte solo se l'area esce dalla vista. Lo storico incendi si nasconde durante lo scenario.
- **Rischio di oggi** (`LivelloRischio.vue`, app e cruscotto, spento di default): celle 2 km sotto lo storico, scala priorita' continua macchia (0,3) -> ambra (0,55) -> brace (0,8), opacita' 42% a zoom 7 che scende a 22% a zoom 11; legenda a gradiente Basso / Medio / Alto, ora di aggiornamento, avviso ambra se `meteo_simulato`.
- **Missioni mirate dal rischio** (app): in cima alla scheda Missioni, badge "dal rischio" brace; card con pillola rischio (medio ambra, alto brace, molto alto brace piu' pieno) + Target, titolo, motivo coi dati, distanza dal centro, punti, scadenza, "Fatta" macchia. Sulla mappa pin `.pin-mirata` 28 px (Target ambra/brace su `fondo-3`); tocco -> flyTo e cerchio tratteggiato ambra di 1 km, poi modalita' "scegli punto".

## Cruscotto su telefono

Sotto 768 px il cruscotto segue lo schema delle app di mappe (desktop invariato, `mobile` da `matchMedia` in `cruscotto.vue`):

- **Mappa a tutto schermo**; colonna destra identica all'app (Livelli -> zoom -> "i", passo 14 px, 58 px sotto il bordo dell'header), sparisce in dissolvenza quando il foglio la coprirebbe.
- **Header a una fila**: pillola 44 col solo marchio, pillola contatori brevi (icone `Inbox` / `CircleCheck` / `MapPin` + cifre, etichette solo per lettori di schermo) chiusa dal `.punto-vivo` (verde in diretta, ambra in riconnessione; con errore diventa pulsante "riprova"), tema compatto a destra.
- **Foglio Segnalazioni** `sospeso` a tre altezze: chiuso 64 px + safe-area (maniglia + "N in coda · priorità max X" / "Tutto tranquillo"), metà 50%, alto 85%. Alto sempre quanto lo stato massimo e spostato con `transform` (320 ms easing in uscita, niente con reduced-motion); trascinamento con pointer events sulla maniglia/intestazione, aggancio allo stato più vicino alla posizione proiettata con la velocità, tocco = chiuso <-> metà. La parte fuori schermo si compensa con padding in fondo all'elenco.
- **Dettaglio nel foglio**: indietro + titolo nell'intestazione, `CorpoScheda` (foto, posizione, priorità scomposta); la selezione (elenco o pin) porta il foglio almeno a metà e fa `flyTo` con padding in basso pari al foglio. Piede fisso con Conferma / Falso allarme (o badge di stato in sola lettura), nascosto a foglio chiuso.
- **Componenti condivisi** desktop/telefono: `SchedeStato` (controllo segmentato, `grande` = 44 px), `ElencoSegnalazioni`, `CorpoScheda`.
- **Legenda** delle priorità in fondo al pannello Livelli (sezione "Legenda"); incendi, hotspot, storico e mappature hanno la loro accanto al livello. Il pannello scorre dentro `maxAltezza` (fino a 14 px sopra il foglio chiuso); aprendolo il foglio scende a chiuso.
- **Popup hotspot** (`PopupHotspot.vue`, `clicHotspot()`): icona Satellite in brace, titolo = comune, ora locale Europe/Rome + relativo, metriche tabulari (affidabilita' a parole+colore, FRP, temperatura K/°C, satellite, diurno/notturno), riga tenue di fonte; i pin delle segnalazioni vincono sull'hotspot, l'hotspot su storico e mappature.
- **Popup**: `impostaFasceLibere()` in `useMappa.ts` (fascia bassa = altezza del foglio, destra = colonna 70 px); larghezza `min(280px, 100vw - 94px)`; si chiudono (`chiudiPopup()`) quando il foglio sale.
