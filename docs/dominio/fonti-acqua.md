# Fonti dati acqua Sardegna (Challenge 4, GreenLab 16-17 ott 2026)

Analisi del 2026-10-09. Verifiche fatte con fetch + curl; nessun login, nessun account.

## Tabella riassuntiva

| Fonte | Dati | Formato | Accesso | Automatizzabile |
|---|---|---|---|---|
| sardegnacedoc.it/invasi/volumi | Volumi invasati per 16 zone / ~33 invasi, 4 snapshot mensili | Tabella HTML | Libero | Si (scraping); `/invasi/csv` risponde 403 al curl |
| Autorita di Bacino /invasi/ | Bollettino mensile invasi + indicatore siccita | PDF mensili (2025-26), ZIP annuali (2009-24) | Libero | Parziale (PDF) |
| ENAS | Anagrafica laghi artificiali; bollettini giornalieri non pubblici online | Pagine HTML per invaso | Libero (solo schede) | Limitato |
| ARPAS idrologia (link sardegnaambiente) | Annali idrologici, serie storiche livelli/portate/piogge, curve di deflusso | PDF + ZIP (serie fino 2013) + dashboard ArcGIS | Libero | Parziale |
| dighe.eu dati tecnici | Dati tecnici grandi dighe (quote, volumi, scarichi) | Tabella HTML unica | Libero | Si (one-shot, statico) |
| GEDI derivazioni idriche | Concessioni/prelievi (sotterranei e superficiali) | Web app | SPID/CIE/CNS, solo enti e concessionari | No |
| CeDoc (monitoraggio) | Banca dati acque, rete termopluviometrica, indicatori invasi | WebGIS pubblico + portale riservato | WebGIS libero; resto SPID | Solo WebGIS |
| Report Osservatorio feb 2025 | Stato severita idrica distrettuale, sintesi | PDF 8 pag, testo estraibile | Libero | Si ma solo testo narrativo |
| ISTAT 2019 | Utilizzo e qualita risorsa idrica Italia | PDF scansione immagine (8 MB, 1 pag.) | Libero | No (serve OCR); dato 2019 |
| Abbanoa Segnalazioni | Segnalazioni guasti/disservizi (distretto, comune, via, stato) | CSV | Libero, licenza "proprietaria" | Si |

## Per fonte

**sardegnacedoc.it/invasi/volumi** - Tabella HTML con volume autorizzato e volume invasato + % per 4 snapshot (08-2026, 07-2026, 06-2026, 08-2025), totali per zona e generale. Unita non dichiarata (verosimilmente Mm3). Aggiornamento mensile. Menu: Indicatori, Bollettino, Mappa, "Aggiornamento volumi" -> `/invasi/csv` (403 da curl senza browser: provare con User-Agent/Referer o dal browser). Contatto: cedoc@regione.sardegna.it. Nessuna licenza esplicita. E la fonte migliore per un MVP.

**Autorita di Bacino /invasi/** - Bollettino "Situazione dei bacini sardi": PDF mensile (ultimo 31/08/2026: ~1.230 Mm3, 66,6%, indicatore siccita 0,49 = preallerta/vigilanza), ZIP annuali 2009-2024, PDF metodologia. Sottosistemi Medio Flumendosa e Nord Occidentale dal 03/2025. Footer "ultimo aggiornamento 2023" obsoleto ma i contenuti sono aggiornati. Utile per storico (ZIP) e indicatore siccita.

**ENAS** - Sito: https://www.enas.sardegna.it (la radice risponde 200; `/it/` e 404). Sezione `/il-sistema-idrico-multisettoriale/laghi-artificiali/<invaso>.html` con una scheda per ogni lago (Cantoniera, Cuga, Monte Pranu, Monte Su Rei, Liscia, ecc.): anagrafica, non serie temporali. I bollettini giornalieri (volumi, % riempimento, afflussi) esistono ma risultano usati solo in letteratura; non trovata una pagina pubblica con serie. Utile per anagrafica/descrizioni, non come feed.

**ARPAS idrologia** (sardegnaambiente.it, pagina aggiornata 03/07/2026) - Annali idrologici 2012-2025 (PDF), serie storiche in ZIP (livelli 1930-2013, portate 1923-2013, piogge 1922-2011, temperature 1988-2002), curve di deflusso ~35 stazioni, report eventi 2018-2026, dashboard ArcGIS real-time (probabile endpoint REST interrogabile: da verificare dalle richieste di rete). Download libero. Serie fermi al 2013: utili per baseline, non per attualita.

**dighe.eu** - Sito personale (ing. Ghinami), non ufficiale. Tabella HTML densa con numero d'archivio MIT, corso d'acqua, tipo, altezza, volumi, quote massime. Nessuna data di aggiornamento. Ottima per arricchire l'anagrafica invasi (join per nome); parsing fragile (colonne stipate), da fare una volta sola.

**GEDI** - Modulo CeDoc per derivazioni idriche (sotterranee e superficiali), volumi prelevati dichiarati dai concessionari. Accesso SPID/CIE/CNS riservato a operatori Province/Genio Civile, concessionari, Autorita di Bacino. Non accessibile ne automatizzabile in hackathon. Eventuale via: richiesta dati agli organizzatori.

**CeDoc monitoraggio** - Centro di documentazione del bacino: acque superficiali/sotterranee, balneazione, rete termopluviometrica, indicatori invasi, derivazioni, scarichi. WebGIS di consultazione pubblico (verificare se espone servizi WMS/WFS); portale con Anagrafiche, GEDI e CEDOC BI solo SPID. Non autenticato, solo descritto. Pagina aggiornata 05/2023.

**Report Osservatorio feb 2025** - PDF Word 8 pagine, taggato, testo estraibile con pdftotext (verificato). Indice: premesse, descrizione SIMR, stato di severita distrettuale, sintesi situazione, link a dati invasi/indicatori. Contenuto prevalentemente narrativo, senza tabelle dati strutturate; trasmesso a ISPRA (isprambiente.gov.it SeverIdrica). Utile come contesto e per i link, non come dataset.

**ISTAT 2019** - PDF di 1 pagina che e una scansione a 300 dpi (nessun testo); dati nazionali, ottobre 2019, non specifici per la Sardegna. Serve OCR, valore basso per la piattaforma. Per dati ISTAT strutturati usare IstatData/SDMX (api.istat.it) sul tema acqua.

**Abbanoa Segnalazioni** - CSV scaricabile da https://www.abbanoa.it/customexport/dataset-csv_dataset-769 (verificato: 200, text/csv, ~2.280 righe). Colonne: Data segnalazione, identificativo, Distretto, Comune, Localita, Via, intervento, Stato ("In corso"/"Sopralluogo eseguito"). Solo segnalazioni aperte o chiuse da <15 giorni; aggiornamento orario dichiarato (le righe viste sono del 13/08/2026: controllare freschezza). Licenza proprietaria, riuso da chiarire. Nessuna coordinata: serve geocoding per comune/localita.

## Link rotti / anomalie

- Nessun link degli organizzatori e rotto. Anomalie: `sardegnacedoc.it/invasi/csv` 403 da curl; `enas.sardegna.it/it/` 404 (usare la radice); footer Autorita di Bacino datato 2023; CSV Abbanoa con date non recenti; ISTAT PDF senza testo.
- Dichiarazione: i risultati sul PDF Osservatorio e ISTAT derivano da estrazione automatica; CeDoc/GEDI non sono stati autenticati.

## Fattibilita challenge 4 in 2 giorni

**Fattibile come MVP, con scope ridotto.** Dati davvero liberi e machine-readable: volumi invasi (HTML), Abbanoa CSV, tabella dighe.eu, serie ARPAS. Manca un feed pubblico di consumi: GEDI (prelievi) e SPID, quindi "consumi idrici" va riformulato come stato della risorsa + criticita rete.

Piano minimo:
1. Scraper `sardegnacedoc.it/invasi/volumi` -> tabella pulita (invaso, zona, volume, %, data), cron/refresh mensile.
2. Backfill: ZIP storici Autorita di Bacino 2009-2024 (da ispezionare) per trend e confronto anno su anno.
3. Arricchimento anagrafica con dighe.eu + schede ENAS (join per nome invaso).
4. Layer Abbanoa CSV: segnalazioni per comune/distretto (geocoding semplice su comune).
5. Frontend: mappa invasi + serie storica + indicatore siccita (0-1, soglie: ordinario/vigilanza/pericolo/emergenza) + contatore guasti in corso. Stack consigliato: FastAPI + PostgreSQL/DuckDB, MapLibre.

Rischi: nessuna licenza esplicita (citare la fonte, dato pubblico), nomi invasi disallineati tra fonti, 403 anti-bot sul CSV invasi, niente dati di consumo reali. Da chiedere agli organizzatori: accesso a GEDI/CeDoc BI o dump, e licenza Abbanoa.

Verdetto: sforzo medio-basso (circa 1 giornata per pipeline + 1 per UI). Fattibile in parallelo alla challenge principale solo con 1-2 persone dedicate.
