<inputs>
Project: "Nurax" (precedentemente "Sentinelle"). Un prodotto reale e funzionante orientato alla prevenzione e geolocalizzazione degli incendi in Sardegna:
App mobile citizen-centric (interfaccia mobile, lingua italiana) e dashboard operatori COP.
Fonti di verità e specifiche di progetto incentrate su: UX ad attrito zero, validazione incrociata contro falsi allarmi, bollettini CFD Protezione Civile, geofencing domestico.
Audience: Giuria dell'hackathon, film proiettato in sala. Punteggio 1-5 su idea, prototipo, novità, impatto sociale, team, presentazione.
In 30 secondi il film deve rendere ovvi idea, novità e impatto, provando che il prototipo è reale e funzionante.
Canvas: 1920x1080, 60 fps, 30 s a 120 BPM (15 battute).
Tutti i testi a schermo in italiano, brevi, incisivi, senza gergo tecnico.
Asset visivi: schermate reali delle app, logo ufficiale (quadrato smussato rosso, contorno fiamma bianca), colori e font da tema.css (Atkinson Hyperlegible), colonna sonora ritmica composta in codice con Web Audio API.
</inputs>

<facts>
Elementi chiave mostrati a schermo (aderenti al prodotto reale):
- Un cittadino apre l'app, tocca SEGNALA, scatta una foto, sceglie Incendio / Fumo / Terreno a rischio, aggiunge una nota opzionale (dettatura vocale), invia. La posizione e la direzione dello sguardo viaggiano con la segnalazione.
- La mappa: posizione dell'utente con cono di direzione, vista satellitare o standard, zone di rischio per livello, cerchi attorno alle segnalazioni attive, pin che si aggregano quando si zooma out, banner di pericolo in tempo reale ("Incendio a 1,0 km da Casa, verso nord-est").
- Luoghi salvati (Casa, Terreno) con avvisi classificati (Urgente / Importante). Conferme crociate della community ("Lo vedo anch'io" / "Non c'è più").
- Gli operatori ricevono la segnalazione pre-filtrata e ordinata per priorità, integrata con hotspot satellitari e dati storici. La conferma "Mezzi sul posto" si illumina in tempo reale sul telefono del cittadino.
- Funziona via browser mobile senza installazione; la mappa di base funziona anche offline.
</facts>

<direction>
Un trailer di lancio di 30 secondi in stile "Apple iPhone Event" che persuade la giuria con un ritmo incalzante, design minimalista e motion actions impeccabili. 
- **Oggetto conduttore (Through-line):** Il pin di segnalazione rosso (disco rosso cerchiato con anello a impulsi) che si trasforma fluidamente in ogni schermata e diventa il logo finale.
- **Stile Visivo & Motion:** Ricostruzione in vettoriale/HTML dei componenti UI reali, animazioni a molla (springs) fluide e naturali, zoom della telecamera in stile product-studio (senza mai fermarsi, transizioni continue tra una scena e l'altra). 
- **Liquid Glass:** Utilizzo di layer in stile Apple Liquid Glass (sfondo traslucido neutro, backdrop-filter blur, riflessi sui bordi) per didascalie, pillole e callout attorno all'interfaccia.
- **Regole ferree:** Zero particelle fte, zero bagliori esagerati, zero transizioni crossfade pigre. Ogni battito della musica (120 BPM) muove un elemento grafico o cambia inquadratura.
</direction>

<structure>
120 BPM (1 battuta = 2 s). Storyboard temporale:
- Hook (Battute 1-2): Il problema in poche parole con grandi caratteri interrotti dall'oggetto conduttore ("Chi lo vede per primo?").
- Centrale (Battute 3-12): 4 momenti chiave in rapida sequenza:
  A. Tre tap rapidi: SEGNALA, foto, invio (La nascita del pin).
  B. Validazione intelligente: La segnalazione incrocia dati meteo e satellitari ottenendo priorità.
  C. Due interfacce, un'unica verità: La dashboard operatore riordina le priorità; "Mezzi sul posto" si accende sullo schermo del cittadino.
  D. Intorno a te: Zoom indietro sulla mappa, cerchi di rischio, banner di pericolo e avvisi per la "Casa".
- Payoff (Battute 13-15): Il momento clou sul beat più forte, trasformazione dell'oggetto nel logo, schermata finale con nome del progetto, CTA d'impatto e crediti.
</structure>

<build>
1. Generare un file HTML standalone a 1920x1080 in `docs/pitch/trailer/`.
2. Animazioni guidate dal tempo (senza timer di stato per evitare sfasamenti).
3. Sfera audio generata in codice tramite Web Audio API (OfflineAudioContext) con cassa su ogni battito e hit sui cambi scena, esportata in WAV/MP3 sincronizzato.
4. Rendering a 60 fps tramite Playwright ed esportazione in MP4 ad alta qualità.
</build>