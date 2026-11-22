# Trailer

Film di 60 s per la giuria (prompt: `docs/pitch/trailer-prompt-2.md`): 1920x1080, 60 fps, 120 BPM, 30 battute da 2 s.
Uscita: `sentinelle-trailer.mp4` (H.264 + AAC 320k), colonna sonora anche in `colonna.wav`.

## Comandi

Da questa cartella, con lo stack Docker acceso (`./scripts/docker.sh`) e i dati demo (`scripts/semina_cop.py`):

```bash
npm install                      # playwright, una volta
node cattura.mjs                 # schermate reali in schermate/ + schermate/meta.js (circa 4 minuti)
node cattura.mjs dashboard       # solo una sezione: segnala, mappa, viaggio, dashboard
node rendi.mjs                   # colonna.wav + sentinelle-trailer.mp4 (fotogrammi a ffmpeg su stdin, circa 8 minuti)
node rendi.mjs --da 34 --a 42 --fps 30            # anteprima.mp4 di un tratto
node rendi.mjs --fotogramma 36.5,51.6 --cartella /tmp/f  # PNG singoli da controllare
```

Anteprima con audio: aprire `trailer.html` nel browser (spazio = play, frecce = un fotogramma, `#t=12.5` = salta).
Le catture vanno rifatte tutte insieme: i "minuti fa" di app e dashboard devono coincidere (se i dati demo sono vecchi,
prima `scripts/semina_cop.py`).

## Come e' fatto

- `trailer.html`: ogni fotogramma e' funzione del tempo (`render(t)`), animazioni a molla calcolate, nessun timer; tempi
  nella tabella `T`. Colonna sonora composta nella stessa pagina con `OfflineAudioContext` (re minore, cassa su tutti i
  120 battiti, colpi a 10, 20, 28, 36, 42, 50, 54, 56 s, finale in Re maggiore), normalizzata a -1 dBFS.
- Apertura: `media/intro-incendio.webm`, 7 s tagliati da "Madeira Forest Fire at Ribeira da Tabua area filmed from ER110
  above (2017)", Strinder, CC BY 3.0 (Wikimedia Commons), citato nei titoli di coda. In resa ogni fotogramma del video
  si cerca e si disegna su una tela.
- `schermate/`: catture reali dell'app (:3000, 393x793 a 3x, barra di stato disegnata sopra) e della dashboard
  (:3001, 1920x1080 a 2x, anche la mappa dopo "Vedi sulla mappa"). Pin, gruppi di pin, punto blu e Casa nella scena D
  sono ricostruiti in HTML con le misure di `webapp/app/assets/css/tema.css`, sopra mappe senza interfaccia catturate a
  piu' livelli di zoom. MapLibre usa tessere da 512 px: le proiezioni geografiche nel trailer ne tengono conto.
- Notifica all'operatore: il contatore reale della scheda Segnalazioni sale da 2 a 3 (la dashboard non ha avvisi a
  comparsa: le segnalazioni entrano in coda in tempo reale).
- Soccorsi: la dashboard non ha un pulsante "invia mezzi"; la flotta simulata del backend manda i 3 mezzi di terra piu'
  vicini a 50 km/h (elicotteri a 200 km/h). Il trailer ricostruisce questo con le basi reali di `GET /basi` (VVF Cagliari
  7,5 km, CFVA Cagliari 11,7 km, VVF Elmas 12,7 km, elicotteri AIB Pula 36,8 km) e le icone disegnate come in
  `frontend/app/composables/useMappa.ts`; i minuti sono distanza / velocita', il viaggio e' compresso in tre secondi.
- Dati: quelli demo nel database (gruppo Settimo San Pietro: 3 segnalazioni, 7 conferme, priorita' 63). Gli stati di
  passaggio (invio, certificazione, soccorritori allertati, mezzi sul posto) sono risposte API intercettate nel browser di
  cattura: `cattura.mjs` blocca ogni richiesta non GET, nel database non si scrive.
- Trappola: la dashboard ha un service worker che scavalca `page.route` di Playwright. Senza
  `serviceWorkers: 'block'` le risposte finte non arrivano e "Certifica incendio" scrive davvero. Certificare un gruppo
  chiama anche `/segnalazioni/{id}/conferma` per gli altri membri.
- Dashboard catturata con Inter al posto del font di sistema (in Linux headless sarebbe DejaVu; su Mac e' SF Pro).
- Font (tutti OFL) in `fonts/`, licenze in `fonts/FONTI.md`. Foto della segnalazione: `dati/demo_foto/fiamme-1.jpg`
  (pubblico dominio), la stessa che l'operatore vede in dashboard.

## Scaletta (secondi)

| s | |
|---|---|
| 0-6 | video di un incendio in montagna; "In Sardegna, ogni anno / 1.300 incendi." (cifre a rulli, fonte CFVA 2005-2025); dissolvenza sul palco |
| 6,5-10 | "Ogni minuto conta." / "Chi lo vede per primo" e il pin rosso al posto del "?" |
| 10-20 | tuffo nel pin che diventa il pulsante SEGNALA; "Tre tocchi.": foto, "Incendio", nota dettata, Invia; nasce il pin; "Posizione e direzione: incluse" |
| 20-28 | il pin atterra sulla mappa satellitare e viaggia fino alla "Centrale operativa" (Cagliari); "In pochi secondi, / arriva già verificata."; si agganciano Satellite, Meteo, Vegetazione, Incendi passati, conferme dei vicini; "Priorità alta" |
| 28-31 | dashboard: "Il cittadino vede." / "L'operatore decide."; il pin entra nel contatore Segnalazioni (2 -> 3), "Nuova segnalazione, già verificata"; la segnalazione sale in cima alla coda |
| 31-35 | validazione (7 conferme, priorità 63 alta), "Certifica incendio", avviso reale; sul telefono "Soccorritori allertati" |
| 35,5-39 | "Vedi sulla mappa": la mappa si inclina, "I soccorsi partono subito.": tre mezzi di terra e un elicottero arrivano da dietro con i minuti che scendono fino a "Sul posto" |
| 39-42 | sul telefono "Mezzi sul posto"; "Una sola verità, in tempo reale." |
| 42-50 | "Ti avvisa se brucia vicino a casa.": banner "Incendio a 0,9 km da Casa", pin Casa e 0,9 km, zoom indietro con i pin che si raggruppano, avvisi Urgente / Importante; il gruppo di pin diventa il pin conduttore |
| 50-53 | "Dalla segnalazione alla centrale, in pochi secondi." / "Visto prima." / "Spento prima" con il pin come punto |
| 53-60 | anello, il pin diventa il logo; "Sentinelle", "Mille occhi sul territorio.", "Diventa sentinella.", crediti, evento, fonti; il film finisce sul quadro completo |
