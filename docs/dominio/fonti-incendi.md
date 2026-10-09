# Fonti dati incendi Sardegna (verifica del 2026-10-09)

Legenda: [VERIFICATO] = provato con richieste reali; [DA VERIFICARE] = non confermato.

## 1. sardegnaambiente.it - Catasto comunale incendi (guida)
- Cosa c'è: solo pagina informativa (L. 353/2000, D.L. 120/2021, L. 155/2021): obbligo dei comuni di istituire il catasto delle aree percorse dal fuoco e aggiornarlo ogni anno; rilievi CFVA disponibili entro il 1 aprile. Divieti art. 10 solo su bosco e pascolo.
- Anni: perimetrazioni dal 2005; tipologie soprassuolo (bosco/pascolo/altro) dal 2009 (la pagina; il WFS espone tipologie dal 2005).
- Formato/CRS/licenza: non indicati. Nessun link diretto ai file: rimanda al Geoportale (cercare "incendi"/"cfva") e al visualizzatore https://www.sardegnageoportale.it/webgis2/sardegnamappe/?map=aree_tutelate
- Contatti: cfva.aiblogistica@regione.sardegna.it (Servizio Antincendio), cfva.urp@regione.sardegna.it
- Limite: zero dati, solo contesto normativo e semantica dei campi bosco/pascolo/altro.

## 2. SardegnaSIT "Aree Tutelate" (webgis2/sardegnaSIT/pc/index.jsp?mapName=AreeTutelate)
- E' un navigatore WebGIS dinamico (app JS): WebFetch non restituisce layer. [DA VERIFICARE] elenco layer.
- Non e' la fonte degli incendi: "Aree Tutelate" = aree protette (Natura 2000, parchi ecc.). Utile solo come layer di contesto (zone da proteggere), non per i perimetri.
- I perimetri incendi sono nei dati scaricabili/WFS (fonte 3).

## 3. webgis2.regione.sardegna.it/download/ (SITR DB Unico) - FONTE PRINCIPALE
Pagina di elenco con link a ZIP/SQLite e schede metadati GeoNetwork (`https://webgis2.regione.sardegna.it/geonetwork/srv/ita/catalog.search#/metadata/R_SARDEG:<UUID>`). Nessuna registrazione richiesta [VERIFICATO: download anonimo riuscito].

### Dataset incendi
| Dataset | URL diretto |
|---|---|
| Perimetri CFVA 2005-2025 (1 ZIP/anno) | `https://webgis.regione.sardegna.it/scaricocartografiaETL/cfva/areeIncendiatePerim{AAAA}.zip` |
| Tipologie soprassuolo CFVA 2005-2025 | `https://webgis.regione.sardegna.it/scaricocartografiaETL/cfva/areeIncendiateTipol{AAAA}.zip` |
| Carta Pericolo AIB 2023-25 | `.../scaricocartografiaETL/protezioneCivile/exp_pericolo_23.zip` |
| Carta Rischio AIB 2023-25 | `.../protezioneCivile/exp_rischio_23.zip` |
| Pericolo / Rischio incendio boschivo e interfaccia 2017 | `.../protezioneCivile/pericolo_incendio_boschivo_2017.zip`, `.../rischio_incendio_boschivo_2017.zip` |
| Vincolo idrogeologico RDL 3267/1923 | `.../pai/VincoloIdrogeologicoRDL_3267_1923.zip` |

### Campione scaricato [VERIFICATO]
Cartella: `/private/tmp/claude-501/-Users-alessandrococco-Documenti-Locale-Programmazione-Projects-hackaton-incendi/4ea678ea-06ab-4d59-b687-b387d1b6f877/scratchpad/incendi/` (z/ = zip, x/ = estratti). Ispezione con parser Python -I (ogrinfo locale rotto per dipendenza abseil mancante).
- `areeIncendiatePerim2025.zip`: 3,06 MB (shp 4,1 MB), file `PERIMETRI-2025.{shp,shx,dbf,prj,cpg,qmd}`, date file 14/04/2026. **1362 poligoni** (Polygon type 5), una riga per incendio/porzione.
  - Campi: ID, COD_INCEND (es. 2025/CA/0005), STIR (ispettorato), DATA (stringa gg/mm/aaaa), STAZIONE (stazione forestale), PROV, COMUNE, TOPONIMO, TIPOLOGIA (ALTRO, BOSCO, PASCOLO e combinazioni), BOSCO_MQ, PASCOLO_MQ, ALTRO_MQ, TOTALE_MQ, BOSCO_HA, NOBOSCO_HA, TOTALE_HA.
  - Esempio: 2025/CA/0248, 15/06/2025, Guasila, loc. Monte Sebera, 216,26 ha (bosco 64,57 ha).
  - Distribuzione: 1149 su 1362 solo "ALTRO" (agricolo/non bosco); molti piccoli (<1 ha).
- `areeIncendiateTipol2025.zip`: 3,28 MB. **1515 poligoni** (un poligono per tipo di soprassuolo). Campi: ID, COD_INCEND, ANNO, PROV, STIR, STAZIONE, COMUNE, TOPONIMO, DATA, TIPOLOGIA (ALTRO/BOSCO/PASCOLO), TOTALE_MQ, TIPO_INCE (vuoto).
- Bbox: E 432822-565009, N 4307508-4563573 = tutta l'isola.
- Il dato 2025 contiene incendi da aprile ad agosto 2025 [DA VERIFICARE copertura fino a fine anno].
- Attenzione: PROV differisce fra layer perimetri e tipologie per lo stesso incendio (es. SU vs VS/CA): usare COD_INCEND come chiave, non PROV.
- 2024: la prima richiesta ha dato 503 e il retry timeout; il server e' intermittente (503/timeout). Mettere in cache i file.

### CRS
- `.prj`: "RDN2008_UTM_zone_32N" (GRS80, meridiano centrale 9, false easting 500000). Equivalente pratico a EPSG:32632 (WGS84 UTM32N, differenza sotto ~1 m) ma etichettato RDN2008 (EPSG:6707/7791). Non e' Monte Mario/Gauss-Boaga (3003) per il 2025; anni vecchi [DA VERIFICARE] (il WFS dichiara EPSG:7791 per 2025).
- Le coordinate del WFS servite in EPSG:4326 vengono con quota Z=0 (3D); ignorare Z.

### Licenza
- Note legali Geoportale: dati RAS sotto CC BY 4.0 se nei metadati "Limitazioni d'uso" = "Nessuna limitazione d'uso"; altrimenti valgono i metadati (possibile rimborso costi). Obbligo: attribuzione, link alla licenza, indicare le modifiche. WFS Capabilities: Fees=NONE, AccessConstraints=NONE. [DA VERIFICARE] la scheda GeoNetwork dei singoli dataset CFVA.

### OGC (WFS) [VERIFICATO]
- Endpoint GeoServer: `https://webgis2.regione.sardegna.it/geoserver/dbu/ows` (WFS 1.0.0/2.0.0). Capabilities 273 KB, risposta rapida.
- Layer: `dbu:areeincendiateperim{2005..2025}`, `dbu:areeincendiatetipol{2005..2025}`, `dbu:exp_pericolo_23`, `dbu:exp_rischio_23`, `dbu:pericoloincendioboschivo_2017`, `dbu:rischioincendioboschivo_2017` (e molti altri: PAI ecc.).
- GeoJSON diretto con riproiezione server-side in 4326, provato:
  `https://webgis2.regione.sardegna.it/geoserver/dbu/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=dbu:areeincendiateperim2025&outputFormat=application/json&srsName=EPSG:4326` (aggiungere `&count=N` o `&cql_filter=...`).
  Proprieta' in minuscolo (cod_incend, data, comune, toponimo, tipologia, totale_ha...), piu' bbox per feature.
- CORS: `Access-Control-Allow-Origin: *` [VERIFICATO] -> chiamabile direttamente dal browser/app web, senza proxy.
- Shapefile via WFS: `outputFormat=SHAPE-ZIP`.
- WMS: endpoint atteso `.../geoserver/dbu/wms` ma GetCapabilities in timeout (60 s) in 2 prove [non confermato]. Per le tile usare altro: vedi sotto.
- Nessuna API key, nessuna registrazione.

### Alternative/cataloghi
- Metadati/INSPIRE: record `R_SARDEG:*` sull'INSPIRE Geoportal (CFVA perimetri 2009, 2020; tipologie 2008/2017/2020). Precisione: confini rilevati con GPS 5-10 m; soglia minima 1000 m2 (da metadati 2009/2020).
- dati.regione.sardegna.it: non ho trovato il dataset diretto (ricerca web negativa) [DA VERIFICARE].

## 4. SardegnaSIT navigatori (www.sardegnageoportale.it/navigatori/sardegnasit/)
- Homepage con elenco navigatori: Base, DBGT10k, Download raster, Aree Tutelate, Carte Tematiche, PAI, PPR, Strumenti Urbanistici, FotoAeree, Sardegna Mappe (+ link "Area sviluppatori").
- Link "Consulta i dati con il WMS" e "Scarica i dati con il WFS" presenti ma URL non visibili nel testo: il WFS reale e' quello al punto 3. WMS [DA VERIFICARE].
- Licenza: rimanda a Condizioni d'uso e note legali (CC BY 4.0 vedi sopra).
- Download raster: DTM/DSM, ortofoto, DBGT10k in GeoTIFF (utile per terreno/pendenze, pesante).
- Aree protette e Natura 2000 interrogabili come layer di contesto.

## 5. epsg.io
- Servizio gratuito (MapTiler) sul database EPSG ufficiale: ricerca CRS, viewer, export WKT/PROJ/JSON (`https://epsg.io/{codice}.wkt`), pagina /transform; trasformazioni massive via MapTiler Coordinates API (piano gratuito). Licenza non indicata; uso consultativo ok.
- Non e' una fonte dati; serve per le conversioni. Codici utili: 4326 (WGS84, lat/lon, per web/GPS), 3857 (tile web), 32632 (WGS84 UTM32N), 6707/7791 (RDN2008 UTM32N), 3003 (Monte Mario/Italy zone 1, Gauss-Boaga, dati vecchi).
- Pagina "about" non cita la Sardegna.

## Utilita' per challenge 2 e 3 (demo di 2 giorni)

Usabile davvero:
- Storico perimetri bruciati 2005-2025 come layer mappa (GeoJSON da WFS in EPSG:4326, nessun download/conversione locale) per: heatmap/storico per comune, "zone gia' bruciate", ricorrenza.
- Carta del Pericolo/Rischio AIB 2023-25 (`exp_pericolo_23`, `exp_rischio_23`) come sfondo di rischio statico per l'alert (da verificare i campi).
- Challenge 2: segnalazioni utenti su mappa + overlay pericolo/storico; geofence "sei in zona ad alto rischio". Dato in tempo reale NON esiste in queste fonti: sono dati consuntivi annuali (pubblicati ad aprile dell'anno dopo). Le segnalazioni vanno simulate/raccolte dall'app.
- Challenge 3: quiz/missioni con dati reali (es. "quanti ettari bruciati nel tuo comune nel 2025", classifica comuni, prima/dopo), badge per area; COD_INCEND/toponimo per storie locali.

Rischi:
- Server intermittente (503, timeout, WMS non risponde): scaricare PRIMA i GeoJSON (o gli shp) e servirli statici dall'app; non dipendere dal live durante la demo.
- CRS: gli shapefile sono in RDN2008 UTM32N -> convertire in EPSG:4326 per Leaflet/MapLibre (ogr2ogr -t_srs EPSG:4326, o pyproj; oppure `srsName=EPSG:4326` sul WFS). Z=0 nei GeoJSON del WFS.
- Peso: ~3 MB zip/anno, 1300-1500 poligoni con coordinate fitte: semplificare (mapshaper/tippecanoe, o PMTiles/vector tiles) per mobile; non caricare 21 anni interi.
- Campo DATA e' stringa gg/mm/aaaa (non ISO); PROV incoerente tra layer; ~85% piccoli incendi "ALTRO".
- ogrinfo locale non funziona (brew abseil mancante): `brew reinstall abseil re2` o usare Python (pyogrio/pyshp) in venv.
- Licenza CC BY 4.0 (da confermare nelle schede): citare "Regione Autonoma della Sardegna - CFVA" in app.
- Alternativa non verificata per tempo reale/satellite: NASA FIRMS (VIIRS/MODIS) e EFFIS - da valutare in un secondo momento.

## Domande da fare al webinar
1. Esiste un feed (API/WFS) di incendi in corso/segnalati in tempo quasi reale (CFVA, 1515, Protezione Civile), o solo il consuntivo annuale?
2. Si puo' integrare/inoltrare le segnalazioni dei cittadini a CFVA/SIDI o c'e' un canale ufficiale? Quali responsabilita' per falsi allarmi?
3. Licenza esatta dei dataset CFVA, Pericolo/Rischio AIB (CC BY 4.0?) e requisiti di attribuzione per il premio/uso post-hackathon.
4. Il WMS/WFS regionale e' garantito stabile e senza rate limit durante il 16-17 ottobre? Esiste un mirror/dump per la gara?
5. CRS ufficiale per anno (3003 vs RDN2008) e disponibilita' di perimetri 2026 in corso.
6. Dati bollettino pericolosita' giornaliero (Protezione Civile) accessibili via API?
7. Dati utili per gamification (comuni, scuole, aree volontari/ BAR) disponibili e liberi?
8. Vincoli privacy/GDPR per geolocalizzazione dei cittadini e segnalazioni.
