# Cose tagliate di proposito

Cio' che abbiamo consapevolmente rimandato per arrivare alla demo. Senza
questo file esiste solo in chat e sparisce. A fine hackathon diventa la slide
"sviluppi futuri".

Formato di ogni voce: **cos'e'**, **perche' e' stata tagliata**, **cosa
servirebbe per farla**. I numeri non si rinumerano.

---

## 1. Autenticazione reale

**Cos'e'.** Login cittadini e operatori. **Perche' tagliata.** Non si vede in
demo: gli utenti si scelgono da un elenco. **Cosa servirebbe.** SPID/CIE per
operatori, login social o magic link per cittadini.

## 2. Notifiche push

**Cos'e'.** Avviso ai cittadini vicini a una segnalazione confermata e agli
operatori. **Perche' tagliata.** Il polling basta in demo. **Cosa
servirebbe.** Web Push con service worker.

## 3. Moderazione delle foto

**Cos'e'.** Filtro di contenuti inappropriati e dati personali nelle foto.
**Perche' tagliata.** Nessun utente reale in gara. **Cosa servirebbe.**
Classificatore immagini e sfocatura volti/targhe.

## 4. Integrazione con il 1515 e i sistemi CFVA

**Cos'e'.** Inoltro delle segnalazioni confermate al canale ufficiale.
**Perche' tagliata.** Richiede un accordo istituzionale. **Cosa servirebbe.**
API o protocollo concordato con CFVA/Protezione Civile.

## 5. Geofencing in background

**Cos'e'.** Alert di prossimita' anche ad app chiusa. **Perche' tagliata.** Il browser non lo permette: l'alert funziona solo con l'app aperta (`watchPosition`). **Cosa servirebbe.** App nativa o PWA con permesso di posizione in background e Web Push.

## 6. Identita' forte (SPID)

**Cos'e'.** Utenti verificati contro gli abusi. **Perche' tagliata.** Nessun utente reale in gara; l'affidabilita' calcolata dagli esiti la attenua. **Cosa servirebbe.** Accesso SPID/CIE.

## 7. Integrazione con il NUE 112

**Cos'e'.** Passare le segnalazioni confermate e i casi "persone in pericolo" al 112. **Perche' tagliata.** Accordo istituzionale; l'app dice solo "chiama il 112". **Cosa servirebbe.** Protocollo concordato con la centrale unica.

## 8. Limite di segnalazioni per ora

**Cos'e'.** Tetto per utente contro spam e voti ripetuti. **Perche' tagliata.** Non si vede in demo. **Cosa servirebbe.** Rate limit per utente/IP nel backend.
