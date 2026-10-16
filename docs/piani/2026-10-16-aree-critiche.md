# Aree critiche di oggi (bollettino automatico)

> Per agenti: SDD snello (AGENTS.md). Spuntare le checkbox, annotare le deviazioni.

**Stato:** chiuso

**Obiettivo:** la piattaforma legge da sola il rischio per cella e dice dove
guardare oggi e perche': 5-8 zone critiche con motivi dai dati, finestra
oraria di picco e risorse vicine. Il cruscotto non si apre piu' su una mappa
vuota. Base: `rischio_oggi.py`, `cella`, meteo orario, `invaso`.

## Contratto

`GET /aree-critiche` (cache allineata al meteo, 1 h):

```text
{ aggiornato_il, meteo_simulato,
  aree: [ { id, livello: alto|molto_alto, indice: 0..1, centro: {lat, lon},
            area: GeoJSON (unione delle celle della zona), comuni: [nomi],
            nome: "tra Serramanna e Villasor",            # dai comuni principali
            motivo: "Raffiche fino a 45 km/h nel pomeriggio, umidita' 22%, ...",
            picco: { dalle: "13:00", alle: "17:00" },      # ore con rischio meteo massimo
            fattori: [ {chiave, etichetta, valore 0..1, testo} ],  # storico, pericolo, vento, umidita', pioggia
            punto_peggiore: {lat, lon},                    # per "Simula scenario"
            invaso: {nome, distanza_km, riempimento} | null } ] }
```

Zone: celle sopra soglia (alto) raggruppate per contiguita' (vicine), ordinate
per indice massimo, max 8; zone di una sola cella ammesse solo se molto alto.
Motivi solo dai dati, nessuna frase inventata.

## Task

### Task 1: backend
- [x] Modulo `aree_critiche.py` + endpoint; test mirato sul raggruppamento.
- **Verifica:** curl con le zone di oggi (nomi, motivi, picco).

### Task 2: cruscotto
- [x] Pannello "Aree critiche di oggi" (scheda nella colonna sinistra accanto a Segnalazioni o sezione sopra la coda; telefono: nel foglio): elenco con livello, nome, comuni, motivo, picco, invaso; tocco -> flyTo + evidenziazione dell'area sulla mappa; "Simula scenario" dal punto peggiore; scomposizione fattori espandibile. Aggiornamento con l'evento SSE `hotspot_aggiornati` o ogni ora.

### Task 3: app e missioni
- [x] Avviso in alto nell'app se il comune dell'utente e' in una zona critica ("Oggi rischio molto alto nella tua zona tra le 13 e le 17: niente fuochi, segnala subito il fumo"), chiudibile per la giornata.
- [x] Missioni mirate scelte preferibilmente dentro le zone critiche vicine.

### Task 4: consegna
- [x] `linguaggio-visivo.md`, STATO.md.

## Deviazioni

- Soglia adattiva: oltre 0,6 si tengono al massimo le 100 celle piu' alte (con giornate secche le celle "alto" sono ~1000 e formerebbero una macchia unica). Contiguita' a 8 vicini su (i, j).
- Il contratto ha in piu' `celle` (id), usato dalle missioni mirate per preferire le celle dentro un'area (+0,2 solo nell'ordinamento).
- Nomi comuni con l'accento al posto dell'apostrofo catastale ("Senorbì"); "ed" davanti a vocale e.
- Scheda "Aree critiche" accanto a Segnalazioni (componente `VistaCruscotto`); clic sulle aree in mappa non gestito (si seleziona dall'elenco).
