# Piano: webapp cittadino e stack a tre servizi

Specifica: `docs/specifiche/2026-10-16-webapp-cittadino.md`. Verifica finale: `scripts/prova_webapp.py`
(backend) e pagine aperte nel browser a 390 px (webapp) con la segnalazione che compare nel cruscotto.

- [x] 1. Backend: DDL (utente.telefono, segnalazione.video/nota/direzione, localita), POST /segnalazioni con
      video/nota/direzione, `api/cittadino.py` (utenti, localita, avvisi, storico, luogo, cerca)
      File: `infra/schema.sql`, `backend/src/sentinelle/{main,api/segnalazioni,api/gioco,api/cittadino}.py`
- [x] 2. `scripts/prova_webapp.py`: utente -> localita -> segnalazione con foto e video -> storico -> avvisi -> coda cruscotto
- [x] 3. `webapp/`: scheletro Nuxt 4 SPA, token, font in locale, composables (api, sessione, posizione, bussola, avvisi, eventi), layout con barra
- [x] 4. Schermate: Benvenuto, Mappa (cono, stato, pin condivisi, chiama), Segnala (+ inviata)
- [x] 5. Schermate: Localita' (elenco su mappa), Avvisi di un luogo, Nuova localita'
- [x] 6. Schermate: Storico, Profilo (modifica telefono)
- [x] 7. Docker: `webapp/Dockerfile` + nginx, `compose.yaml` (webapp, dashboard, backend separati), dev override, `scripts/docker.sh`, docs
- [x] 8. Verifica end to end nel browser (390 px) e nel cruscotto; screenshot di ogni schermata

Deviazioni e scoperte durante il lavoro: annotate qui sotto.

- Dump `dati-v1`: la webapp crea le sue tabelle all'avvio del backend (DDL idempotente), nessuna ripubblicazione necessaria.
- `npm install` della webapp fallisce con npm 10 senza `legacy-peer-deps` (errore `edgesOut`): c'e' `webapp/.npmrc`.
- Nominatim (ricerca indirizzi e via) richiede rete: senza, `/cerca` ripiega sul centro del comune dichiarando "(centro del comune)".
- Le celle del rischio vanno agganciate alla griglia esatta (indici interi) prima dell'unione, altrimenti restano fessure.
- Servizio compose `frontend` rinominato `dashboard` (porta 3001); la webapp prende la 3000. Chi aveva l'app su :3000/app ora usa :3000.
- Numeri 1515 e 112 della schermata Chiama: da verificare con la Protezione Civile / CFVA.
- Tunnel per il telefono: servizio compose `tunnel` (cloudflared 2026.10.1, profilo `tunnel`) acceso da `scripts/docker.sh`, che stampa indirizzo e QR (qrencode se c'e', altrimenti un container Node usa-e-getta). Il tunnel espone solo la webapp; nginx della webapp lascia passare solo le rotte del cittadino (conferma/archivia/stato/simulazione rispondono 403).

## Secondo giro (2026-10-17): miglioramenti da prova sul telefono

- [x] Mappa: satellite di default con interruttore verso la mappa normale (`useVistaMappa`, `impostaVista`); via crediti, scala e "+/-"; barra dei pericoli `BannerPericolo` a tre toni; pulsante SEGNALA; Chiama solo icona; cerchio attorno alle segnalazioni; fascio dello sguardo sfumato a misura fissa; raggruppamento per vicinanza sullo schermo
- [x] Bug: dopo "nord" la bussola non faceva piu' tornare a me. Causa probabile: `setBearing` del sensore interrompeva il `flyTo` in corso; ora il sensore non gira la mappa mentre si anima e `vaiAMe` imposta anche il bearing
- [x] Segnala: "Allega" commentata (resta nel file), nota facoltativa sempre visibile con microfono; conferma senza priorita' ne' controlli, con la nota nel riepilogo
- [x] Localita': mappa `flex-1`, pannello alto quanto serve (max 62 dvh), dettaglio compatto
- [x] Profilo: tolto "Testo grande" (`useTestoGrande` cancellato), aggiunti i Crediti; testo base 15 px
- Il satellite (Esri) richiede rete: dopo 4 tile in errore la mappa torna alla vista normale e avvisa. Valutare un provider con chiave/licenza prima di un uso pubblico.

## Terzo giro (2026-10-17)

- [x] Mappa: vista iniziale col cerchio dell'incidente intero (`cameraCerchi`, `inquadraIniziale`); tolta la scritta "Guardi verso ..."
- [x] Localita': mappa a tutta altezza e pannello sovrapposto; selezione centrata nella parte libera con `offset`; pin non ricreati a ogni selezione; nessuna scheda aperta all'ingresso
- [x] Conferma segnalazione: riepilogo ingrandito (tipo, dove, nota), bottoni in fondo
- [x] Tutti i pannelli con maniglia: altezza regolabile trascinando (`useAltezzaPannello`, usato da `Foglio` e dall'elenco Localita')
