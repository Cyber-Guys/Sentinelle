# Materiali dell'hackathon

File ufficiali ricevuti dagli organizzatori (sola lettura):

- `Elenco dataset.xlsx`: fonti dati per area tematica (3 fogli).
- Due email di Open Campus (iscrizione, dataset e webinar), sintetizzate sotto.

## Sintesi

- **Evento:** GreenLab Sardegna Hackathon, monitoraggio ambientale.
- **Date:** venerdi' 16 e sabato 17 ottobre 2026, 9:00-18:00.
- **Sede:** Open Campus, Localita' Sa Illetta (S.S. 195 km 2,300), Cagliari.
- **Team:** Nicholas, Andrea, Nicola, Alessandro. Ammessi 3-6 persone;
  l'organizzazione puo' aggiungere membri il primo giorno. Max 50 partecipanti.
- **Conferma iscrizione:** entro il 14 ottobre.
- **Webinar dataset:** mercoledi' 14 ottobre, 17:30, 1 ora, Zoom
  (https://us06web.zoom.us/j/82688302124). Obbligatorio per DIEE/DMI ai fini
  del CFU. Portare domande sui dati.
- **CFU:** 1 CFU (UniCa/UniSS) con frequenza continuativa; per DIEE/DMI servono
  25 ore: ~7 di preparazione individuale (studio dataset + webinar) e ~18 in
  presenza.
- **Supporto:** mentor presenti ogni giorno per dati e progettazione.
- **Formato finale:** pitch finale, poi valutazione della giuria (sotto).
- **Contatti:** info@opencampus.it.

## Valutazione

Dopo tutti i pitch, ogni giurato assegna da 1 a 5 a ciascun criterio (pesi
uguali); segue una consultazione tra giudici che fissa la classifica finale.
Premiato il primo team classificato.

| Criterio | Cosa si valuta | Come lo copriamo |
|---|---|---|
| Idea | Rispondenza alla sfida, fattibilita' tecnica, creativita' | Rispondere letteralmente alla domanda della challenge |
| Prototipo | Tecnologia impiegata e stadio di sviluppo | Demo end-to-end funzionante, dati reali |
| Fattore novita' | Valore aggiunto e grado d'innovazione | Cio' che le app esistenti non fanno |
| Impatto sociale | Benefici per il territorio (economici, culturali, sociali, ambientali) | Numeri sardi: ettari bruciati, comuni, costi |
| Gruppo di lavoro | Coinvolgimento e multidisciplinarieta' | Ruoli chiari, tutti nel pitch, uso dei mentor |
| Presentazione | Originalita' e chiarezza del pitch | Storia + demo live, provata prima |

Implicazione: 4 criteri su 6 non dipendono dal codice. Il prototipo pesa 1/6:
deve funzionare ed essere credibile, non completo.

## Le cinque challenge

| # | Area | Domanda | Output atteso |
|---|---|---|---|
| 1 | Open data | Come risolvere la frammentazione tra i database ambientali sardi? | Dashboard web interattiva che unifica database diversi |
| 2 | Incendi | Come supportare la prevenzione coinvolgendo i cittadini? | App mobile di alert precoce con mappatura partecipata di aree a rischio e focolai |
| 3 | Incendi | Come coinvolgere comunita' locali e giovani nella prevenzione? | Strumento di gamification (mini-game, app a premi, dinamiche interattive) |
| 4 | Acqua | Come ottimizzare gestione e monitoraggio dei consumi idrici? | Piattaforma open-source di raccolta e monitoraggio dei consumi |
| 5 | Open data | Come rendere i dataset ambientali fruibili a tutti? | Portale web con API semplificate |

## Fonti per area (dall'Excel)

Analisi dettagliata di ogni fonte in `docs/dominio/fonti-*.md`.

**Incendi (challenge 2, 3):** perimetri degli incendi >= 1000 mq del Corpo
Forestale (CFVA), con date e vegetazione, in formato GIS nativo.
- Guida: https://www.sardegnaambiente.it/index.php?xsl=611&s=19&v=9&c=4571&na=1&n=10
- Aree tutelate (WebGIS): https://www.sardegnageoportale.it/webgis2/sardegnaSIT/pc/index.jsp?mapName=AreeTutelate
- Download: https://webgis2.regione.sardegna.it/download/
- Navigatore SardegnaSIT: https://www.sardegnageoportale.it/navigatori/sardegnasit/
- Sistemi di coordinate: https://epsg.io/about

**Open data (challenge 1, 5):**
- SardegnaSIRA: https://portal.sardegnasira.it/dati-ambientali
- dati.gov.it: https://www.dati.gov.it/view-dataset

**Acqua (challenge 4):**
- Invasi (CeDOC): https://www.sardegnacedoc.it/invasi/volumi
- Autorita' di Bacino, bollettini: https://autoritadibacino.regione.sardegna.it/invasi/
- ENAS: link mancante nell'Excel
- Dighe: https://www.sardegnaambiente.it/index.php?xsl=611&s=21&v=9&c=93749&na=1&n=10 e https://www.dighe.eu/dati/dati_tecnici.htm
- GEDI: https://www.regione.sardegna.it/servizi/accesso-ai-servizi-on-line/indice-dei-servizi/gedi-banca-dati-derivazioni-idriche
- CeDoc BI (SPID/CNS): https://autoritadibacino.regione.sardegna.it/monitoraggio/cedoc/
- Report Osservatorio feb 2025: https://autoritadibacino.regione.sardegna.it/wp-content/uploads/2025/03/02.-Report-Osservatorio-Sardegna-febbraio-2025.pdf
- Istat: https://www.istat.it/it/files/2019/10/Utilizzo-e-qualit%C3%A0-della-risorsa-idrica-in-Italia.pdf
- Abbanoa, segnalazioni: https://www.abbanoa.it/Documenti-e-dati/Dataset/Segnalazioni
- Nota: le letture orarie dei contatori non sono open data (GDPR).
  Ripartizione dei consumi: agricolo ~70-75%, civile ~20-25%, industriale ~3-5%.
