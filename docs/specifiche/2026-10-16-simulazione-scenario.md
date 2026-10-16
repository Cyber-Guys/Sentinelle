# Simulazione di scenario e rischio di oggi

**Data:** 2026-10-16
**Stato:** approvata

## Intento

Prevedere -> intervenire. Dato un punto (hotspot, segnalazione o punto sulla
mappa) l'operatore vede dove arriverebbe il fuoco nelle prossime ore, fino a
24, con il meteo previsto ora per ora: se il vento gira, il fronte gira. E' il
momento "wow" della demo e trasforma una segnalazione in decisione operativa
(dove mandare i mezzi, quali comuni allertare, quale acqua usare).

Un livello leggero "Rischio di oggi" per cella da' il contesto e alimentera'
le missioni mirate (feature C, dopo).

## Non obiettivi / onesta'

- Non e' un modello validato: automa su griglia con vento, umidita' e
  combustibile stimato. **Niente pendenza** (nessun dato di quota). Il pannello
  lo dice sempre ("Scenario indicativo, modello semplificato").
- Niente machine learning: punteggio trasparente.

## Rischio di oggi

- Griglia di celle ~2 km (0,02° lat x 0,025° lon) sulla Sardegna, solo celle
  dentro un comune. Precalcolata una volta (`scripts/prepara_celle.py`) in
  tabella `cella(id, geom, storico, pericolo)`:
  - `storico`: incendi CFVA 2005-2025 che toccano la cella, pesati per
    recenza (peso 1 nel 2025, ~0,5 nel 2015);
  - `pericolo`: classe AIB prevalente (Basso..Alto -> 0..1).
- Meteo: previsione oraria Open-Meteo su una griglia grossa (~0,25°, ~40 punti),
  cache 1 h; per cella il punto meteo piu' vicino, condizioni peggiori delle
  prossime 24 h.
- Indice 0..1 = combinazione pesata (pesi in `config/pesi.toml`) di storico
  normalizzato, pericolo, meteo (`rischio_meteo` esistente).
- `GET /rischio/griglia` -> `{celle: [[lon, lat, valore], ...], aggiornato_il}`
  (centri cella; il frontend disegna celle o heatmap).

## Simulazione

- `POST /simulazione {lat, lon, ore: 1..24}` ->
  ```text
  {
    origine: {lat, lon}, inizio: ISO, ore, risoluzione_m: 200,
    fotogrammi: [ {ora: 1..ore, area: GeoJSON MultiPolygon, ettari, fronte_km,
                   vento: {kmh, da_gradi}, umidita} ],
    comuni: [ {nome, raggiunto_ora} ]          # primo istante di contatto
    acqua:  [ {nome, tipo, distanza_km, lat, lon} ]  # piu' vicine al fronte finale, max 5
    note: "Scenario indicativo: ..."
  }
  ```
- Algoritmo: griglia 200 m su un dominio 40 x 40 km centrato sul punto (si
  allarga se il fronte tocca il bordo). Tempi di arrivo con un cammino minimo
  (Dijkstra) su 8 vicini; la velocita' di propagazione per passo dipende da:
  - combustibile della cella: pericolo AIB e storico; mare/fuori comuni = non
    brucia;
  - vento dell'ora corrente (velocita' e direzione dalla previsione oraria):
    piu' veloce sottovento, molto piu' lenta controvento;
  - umidita' e pioggia recente dell'ora (rallentano).
  Il meteo varia nel tempo: il passo usa l'ora in cui il fuoco arriva nella
  cella. Ordini di grandezza plausibili (decine di ettari in 1 h, migliaia in
  24 h con vento forte) da tarare con costanti in configurazione.
- Per ogni ora: celle con arrivo <= ora -> unione -> poligono semplificato in
  EPSG:4326.
- Comuni: intersezione dei poligoni con `comune`, ora del primo contatto.
- Acqua: mappature `punto_acqua` piu' vicine al fronte finale (la feature B
  aggiungera' gli invasi).
- Tempo di risposta < 3 s per 24 h.

## Interfaccia (cruscotto, poi app in sola lettura)

- Avvio: pulsante "Simula scenario" nel popup hotspot, nella scheda
  segnalazione e con clic destro / pressione lunga sulla mappa.
- Pannello `sospeso`: scelta orizzonte (1, 3, 6, 12, 24 h), cursore del tempo
  con play/pausa, ora corrente in grande, ettari, vento dell'ora (freccia +
  km/h), elenco comuni con ora di contatto, acqua piu' vicina; nota di onesta'.
- Mappa: aree per ora con gradiente (vecchie tenui, ora corrente brace piena),
  linea del fronte corrente, punto di origine pulsante; le ore successive al
  cursore nascoste. Tasto "Chiudi scenario" ripulisce i layer.
- Livello "Rischio di oggi" nel pannello Livelli (spento di default), con
  legenda; colori della scala di priorita'.
