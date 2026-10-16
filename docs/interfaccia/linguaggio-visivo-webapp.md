# Linguaggio visivo della webapp cittadino (`webapp/`)

Distinto da `linguaggio-visivo.md` (scuro, cruscotto e vecchio `/app`). Nato dal concept G+H della sessione di
design del 2026-10-16. Token in `webapp/app/assets/css/tema.css`.

## Principi

- **Per chi usa poco il telefono, all'aperto.** Chiaro di giorno (si legge al sole), pulsanti grandi (primari
  da 5,5 rem, secondari da 3,25 rem), parole semplici ("SEGNALA", icona del telefono per chiamare), sempre icona + testo.
- **Un solo accento pieno per schermata**, la brace (`#c4360f`), sull'azione principale. Il resto bianco,
  inchiostro e grigi freddi.
- **Stato = colore + parola**, mai colore da solo: etichette `Rischio alto`, `Urgente`, `Confermata`.
- **Misure in rem**: base `html` a 15 px (93,75%). Niente impostazione "Testo grande": il testo e' gia' grande per scelta.
- **Font** Atkinson Hyperlegible Next (leggibilita' in condizioni difficili), incluso nel bundle: niente rete.

## Token

| Ruolo | Valore |
|---|---|
| inchiostro / testo-2 / linea / fondo | `#14181f` / `#566170` / `#d3d9e0` / `#eef1f5` |
| brace (accento, fuoco) | `#c4360f`, premuto `#a82c0b`, fondo `#fde9e2` |
| ambra (medio) | `#f2b441`, testo `#7a4c00`, fondo `#fcefd0` |
| macchia (ok, basso) | `#17704a`, fondo `#d9f0e4` |
| cielo (info, "io") | `#1f55c4`, fondo `#dce7fb` |
| fumo / terra | `#566170` / `#8a5a2b` |

Tipi di segnalazione: Incendio = brace + Flame, Fumo = slate + Cloud, Terreno a rischio = marrone + icona
custom `IconaTerreno` (terra secca con crepe). Priorita' degli avvisi: Urgente (brace piena), Importante
(ambra), Informazione (cielo). Livelli di rischio: basso / medio / alto / molto alto come etichette.

## Componenti (classi in `tema.css`)

`.gigante` (e `.gigante-bianco`), `.pulsante` (+ `-scuro`, `-piccolo`, `-fantasma`), `.tondo`, `.pillola`,
`.scheda`, `.elenco`/`.riga`, `.foglio` (finestre dal basso, componente `Foglio`), `.tessera` (scelta del tipo),
`.opzione` (radio), `.segmenti`, `.scelta`, `.campo`, `.interruttore`, `.etichetta` (+ `e-*`), `.scheletro`,
`.sezioni` (barra a 4 voci), `.toast`. Tre stati per ogni dato remoto: scheletro, `StatoErrore`, `StatoVuoto`.

## Mappa

- **Due viste** (`Vista` in `utils/mappa.ts`, scelta salvata nel telefono, `useVistaMappa`): **satellite** (default sulla
  Mappa; immagini Esri World Imagery, serve rete, con sopra le etichette in bianco) e **mappa** (Protomaps offline,
  `frontend/public/tiles/sardegna.pmtiles`, flavor `light` ritoccato, POI tolti, etichette in italiano). Si passa
  dall'una all'altra con l'interruttore in alto, senza ricaricare. Senza rete il satellite fallisce e si torna alla
  mappa. Le altre schermate (Localita', Profilo, Segnala) restano sulla mappa offline.
- **Nessun controllo di MapLibre** sulla mappa: niente scala, niente "+/-" (si zooma col pizzico), niente crediti.
  I crediti (OpenStreetMap, Protomaps, Esri) stanno nel Profilo.
- **Vista iniziale**: se la barra dei pericoli segnala un incidente, la mappa si apre inquadrando per intero il suo
  cerchio (e quelli delle altre segnalazioni nello stesso punto) insieme a me, se sono entro 6 km (`cameraCerchi`,
  margini per la barra in alto e il tasto in basso). Da una segnalazione dello storico: il suo cerchio. Senza
  incidenti: io, zoom 16 e la mappa mi segue. Con un'inquadratura sull'incidente la mappa non mi segue finche' non
  si preme "torna a me".
- **Io**: punto blu e cerchio di precisione (geografico), poi il **fascio dello sguardo**: marcatore HTML a misura
  fissa in pixel (176 px, spicchio di 56 gradi) che sfuma verso l'esterno con una maschera radiale, come Apple
  Maps, e **non scala con lo zoom**. Niente scritta "Guardi verso ...": la direzione si legge dal fascio. Senza
  bussola: "Attiva la bussola" (iPhone) o "Direzione non disponibile". Per le prove: `?pos=lat,lon` e `?dir=gradi` nell'indirizzo.
- **Pin**: cerchi con icona (`.pin`, colore per tipo o per livello `pin-l-*`), etichetta con il nome, onda sul
  fuoco attivo. Ogni segnalazione attiva ha un **cerchio** attorno (fuoco 350 m, fumo 600 m, terreno 200 m).
  **Raggruppamento**: segnalazioni a meno di 44 px una dall'altra diventano un solo pin con il conteggio, con
  l'icona della piu' grave (fuoco > fumo > terreno; le spente per ultime); un tocco avvicina o, se sono nello
  stesso punto, elenca. **Zone a rischio**: celle 2 km unite per livello (backend), ambra = medio, brace = alto.
- **Barra dei pericoli** (`BannerPericolo`): una riga in cima, tre toni. Verde "Tutto tranquillo", ambra
  "Fumo a 2,3 km" (attenzione), rosso pieno con onda "Incendio a 1,0 km" (pericolo). Sotto il titolo: da dove
  (casa o te), verso quale punto cardinale, da quanto. A destra `+N` se ce ne sono altri; un tocco apre l'elenco.

## Pannelli dal basso

Ogni pannello con la maniglia in alto al centro (`Foglio`, e l'elenco di Localita') ha l'**altezza regolabile
trascinando la maniglia**: su allarga, giu' restringe (`useAltezzaPannello`). Nei fogli sopra il velo, trascinare
molto sotto il minimo (150 px) li chiude; un tocco sulla maniglia alterna altezza naturale e massima (92 dvh);
da tastiera frecce su e giu'. Il contenuto scorre dentro il pannello. La zona da afferrare e' tutta la fascia in alto.

**Localita'**: la mappa occupa tutta l'area e il pannello ci sta sopra (non la ridimensiona: i pin non si spostano
mai da soli). La localita' scelta si porta al centro della parte libera (`offset` di MapLibre, mai `padding`
persistente); dopo aver regolato il pannello la mappa si muove solo se il pannello ha coperto la localita'.
All'apertura nessuna scheda e' espansa: la mappa ha tutto lo spazio.

**Conferma segnalazione**: riepilogo grande in alto (tipo, dove, nota), i due bottoni fissi in fondo.

## Emerso in implementazione

- Nelle colonne a scorrimento (`.scorri`) i figli non devono restringersi: `.scorri > * { flex-shrink: 0 }`.
- I `File` della bozza di segnalazione stanno in `shallowRef`: un proxy reattivo non e' un `Blob` e `FormData` lo rifiuta.
- Il riferimento dell'utente per Segnala e Localita' (immagine generata) e' stato adattato al nostro stile, non copiato.
- Un `export const` con virgole nel tipo o nel valore (es. `Record<A, B> = { x: 1, y: 2 }`) in `utils/*.ts` fa saltare la
  scansione degli auto-import di Nuxt: spariscono altre funzioni dello stesso file ("... is not defined" a runtime).
  Le costanti usate solo nel file non si esportano.
- Gli screenshot a viewport intero di Playwright mostrano un rettangolo chiaro fantasma sopra un `Foglio` ridimensionato;
  con `clip` la schermata e' pulita: e' un artefatto di cattura, non della pagina.
