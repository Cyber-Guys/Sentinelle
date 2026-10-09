# Fonti extra per la demo incendi (GreenLab Sardegna, 16-17 ott 2026)

Verifiche eseguite il 2026-10-09 con curl, senza account né credenziali. "Verificato" = chiamata eseguita con risposta valida oggi.

## Tabella riassuntiva

| Fonte | Dati | API | Chiave | Latenza | Licenza | Verificato |
|---|---|---|---|---|---|---|
| Bollettino pericolo incendi (PC Regione Sardegna) | Livello di pericolo (basso/medio/alto/estremo) per 25 zone di allerta, previsione giornaliera | No (solo PDF/pagina web) | No | Pubblicato entro le 14:00 ogni giorno (1 mag/giu - 31 ott) | Dati pubblici RAS (licenza non verificata) | NO (sito non raggiungibile in modo pulito, vedi sotto) |
| NASA FIRMS CSV pubblico | Hotspot VIIRS SNPP/NOAA-20, Europa 24h/48h/7d | File CSV (non API) | No | NRT, circa 3 h dal passaggio | Open (NASA, citare FIRMS) | SI |
| NASA FIRMS Area API | Hotspot per bbox, giorni 1-5, sorgenti VIIRS_SNPP/NOAA20/NOAA21_NRT, MODIS_NRT | Si (REST CSV) | MAP_KEY gratuita (richiede email, non creata) | RT <= 60 min dal passaggio (NRT standard circa 3 h) | Open | Parziale (endpoint risponde, DEMO_KEY rifiutata: "Invalid MAP_KEY") |
| EFFIS/GWIS WMS | FWI (ECMWF, MF, NASA), hotspot VIIRS/MODIS, aree bruciate NRT e storiche 2016-2025 | Si (OGC WMS) | No | Giornaliera (FWI), hotspot NRT | Copernicus, uso libero con citazione | SI (GetCapabilities e GetMap) |
| Open-Meteo Forecast | Temperatura, umidità, vento, raffiche, pioggia, ET0, VPD, ore orarie/giornaliere | Si (JSON) | No (uso non commerciale, <10k call/giorno) | Aggiornamento orario | CC BY 4.0 | SI |
| Open-Meteo FWI | - | NO: non esiste un indice FWI (parametro `fire_weather_index` rifiutato) | - | - | - | SI (negativo) |
| ARPAS Sardegna | Meteo/clima, bollettini | Nessuna API trovata | - | - | - | NO (arpas.sardegna.it non risponde da qui) |
| Corine Land Cover 2018 (EEA) | Classi uso suolo (311 = bosco latifoglie, 323 = macchia...) | Si (ArcGIS REST identify) | No | Statico (2018; CLC2024 in rilascio) | Copernicus, libero | SI |
| Sardegna Geoportale | Carta uso suolo, forestale, WMS/WFS, download shapefile | Si (WMS/WFS dichiarati) | No | Statico | CC (da verificare per layer) | Parziale (sito OK, endpoint geoserver non raggiungibili da qui) |
| dati.regione.sardegna.it | Open data RAS | NO CKAN API (`/api/3/action` restituisce HTML) | No | Statico | IODL/CC | Parziale (portale OK, non interrogabile via API) |
| OpenStreetMap / Overpass | Strade, sentieri, fire_station, punti acqua (`emergency=water_tank/fire_hydrant`, `natural=spring`) | Si (Overpass QL) | No | Quasi real time | ODbL | Parziale (server `overpass-api.de` risponde ma sovraccarico/timeout oggi) |

## Per fonte

### 1. Bollettino pericolo incendi (Protezione Civile RAS)
- Fonte: Direzione generale Protezione civile, sito `www.sardegnaprotezionecivile.it` e sistema SIPC/Zerogis.
- Formato: PDF "Bollettino di previsione di pericolo incendio" con livello per zona di allerta (25 zone secondo DGR 2856/2026), fasi operative (attenzione, preallarme...). Da fonti secondarie (delibere comunali): pubblicato entro le 14:00; campagna 2026 anticipata al 1 maggio, alto pericolo 1 giu - 31 ott (il 16-17 ott il bollettino e probabilmente ancora attivo ma NON verificato).
- Stato verifica: `https://www.sardegnaprotezionecivile.it` risponde con certificato TLS non valido per quell'host (mostra la home generica RAS), quindi URL esatto del PDF e scaricabilita automatica NON verificati. Nessun feed RSS/JSON trovato.
- Azione: chiedere agli organizzatori / aprire il sito a mano e annotare l'URL del PDF; fallback demo: parsing PDF con `pdfplumber` o dato simulato con le 25 zone. Proposta: stima propria del pericolo per zona (Open-Meteo + FWI EFFIS) come "mini bollettino" live.
- Esempio di PDF storico (formato): `https://www.comune.villacidro.su.it/uploads/allegati/BPI_DEF_del_02-07-2024.pdf`

### 2. NASA FIRMS
- Senza chiave, funzionante oggi (file Europa, 24h, filtrare Sardegna bbox 8.0,38.8,9.9,41.3):
  ```
  curl -s "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Europe_24h.csv" \
   | awk -F, 'NR==1 || ($1>38.8 && $1<41.3 && $2>8 && $2<9.9)'
  ```
  Variante NOAA-20: `.../noaa-20-viirs-c2/csv/J1_VIIRS_C2_Europe_24h.csv` (200 OK). File 7d: `SUOMI_VIIRS_C2_Europe_7d.csv` (48 punti in Sardegna negli ultimi 7 giorni: molti sono probabilmente stoppie/controllati, non filtrati). Colonne: latitude, longitude, bright_ti4, acq_date, acq_time, confidence, frp, daynight.
- Area API (richiede MAP_KEY gratuita, registrazione con sola email su https://firms.modaps.eosdis.nasa.gov/api/map_key/ — non creata):
  `https://firms.modaps.eosdis.nasa.gov/api/area/csv/<MAP_KEY>/VIIRS_SNPP_NRT/8,38.8,10,41.3/1`
  Giorni 1-5, limite 5000 transazioni / 10 min. Sorgenti: VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT, MODIS_NRT (+ _SP archivio). Stato oggi: endpoint attivo (risponde 400 "Invalid MAP_KEY" con DEMO_KEY).
- Limiti: risoluzione 375 m (VIIRS), 1 km (MODIS), 2-4 passaggi/giorno, falsi positivi (agricoltura, industria) -> usare `confidence` e incrocio con segnalazioni cittadine.

### 3. EFFIS / GWIS (Copernicus)
- WMS 1.3.0 GWIS (hotspot + FWI): `https://maps.effis.emergency.copernicus.eu/gwis?service=WMS&request=GetCapabilities&version=1.3.0`
  Layer verificati: `ecmwf.fwi`, `mf025.fwi`, `nasa_geos5.fwi`, `viirs.hs.today|week|month|season`, `viirs.hs.n20.today`, `modis.hs.today|week`. Dimensione `time` (default 2019-01-01: passare sempre `&time=YYYY-MM-DD`).
- WMS EFFIS (aree bruciate): `https://maps.effis.emergency.copernicus.eu/effis?...` layer `effis.nrt.ba.poly`, `effis.nrt.ba.point`, `modis.ba.poly.<anno>` (2016-2025), `mf010.fwi`.
- Esempio GetMap (funzionante, 200 image/png):
  ```
  https://maps.effis.emergency.copernicus.eu/gwis?service=WMS&request=GetMap&version=1.1.1&layers=ecmwf.fwi&styles=&srs=EPSG:4326&bbox=8,38.8,10,41.3&width=512&height=600&format=image/png&transparent=true&time=2026-10-08
  ```
  Usabile direttamente come tile layer in Leaflet/MapLibre (`L.tileLayer.wms`). Nota: GetFeatureInfo non testato con successo (serve il parametro corretto); FWI e solo raster visivo, non numerico semplice. Tabella valori FWI -> classi: 0-5 basso, 5-11 moderato, 11-21 alto, 21-38 molto alto, 38-50 estremo, >50 estremo+ (classi EFFIS).
- Le aree bruciate NRT e il FWI sono a risoluzione ~9 km (ECMWF) / 25 km: grossolane per un'app locale.

### 4. Meteo
- Open-Meteo (nessuna chiave, uso non commerciale): esempio verificato
  ```
  https://api.open-meteo.com/v1/forecast?latitude=40.1&longitude=9.0&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,vapour_pressure_deficit&daily=et0_fao_evapotranspiration,precipitation_sum,wind_gusts_10m_max&timezone=Europe/Rome&forecast_days=3
  ```
  Restituisce vento, raffiche, umidità, VPD (kPa), ET0 e pioggia. FWI: non esiste. Opzione: calcolare in proprio un FWI semplificato (formule Van Wagner / libreria `fwi` o `xclim`) da temperatura, umidità, vento a 24h e pioggia, oppure un indice euristico (alta temperatura + umidità < 30% + raffiche > 30 km/h + giorni senza pioggia). Archivio storico: `https://archive-api.open-meteo.com/v1/archive` (stessi parametri, per pioggia ultimi 30 giorni).
- ARPAS: `arpas.sardegna.it` non risponde da questa rete; nessuna API pubblica documentata trovata (dati meteo e bollettini in HTML/PDF). Non contare su ARPAS per la demo; chiedere agli organizzatori.

### 5. Uso suolo / vegetazione
- Corine Land Cover 2018 (EEA ArcGIS REST, verificato): identify su punto in Web Mercator
  ```
  https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/identify?f=json&geometry={"x":1002000,"y":4930000}&geometryType=esriGeometryPoint&sr=102100&layers=all&tolerance=1&mapExtent=990000,4920000,1010000,4940000&imageDisplay=400,400,96
  ```
  Risposta: `Code_18: 311` (bosco di latifoglie). Classi utili per rischio: 311/312/313 boschi, 321-324 macchia/arbusteti, 243, 211-244 agricolo. Usabile anche come WMS/tile e come classificatore "cosa c'e sotto la segnalazione".
- Sardegna Geoportale (`https://www.sardegnageoportale.it`): carta uso suolo (UDS), carta forestale, aree percorse dal fuoco, con WMS/WFS e download; il sito e raggiungibile ma gli endpoint geoserver testati non rispondono. Da esplorare a mano il catalogo "Download dati" prima dell'hackathon.

### 6. Altri dataset
- Open data RAS: `https://dati.regione.sardegna.it` non espone API CKAN (la chiamata `/api/3/action/package_search` restituisce una pagina HTML). Uso: download manuale dei dataset.
- OSM Overpass (esempio, oggi risponde ma e in timeout per sovraccarico; riprovare o usare un estratto Geofabrik `sardegna-latest.osm.pbf` da https://download.geofabrik.de/europe/italy/isole.html):
  ```
  curl -A "hackathon/1.0" --data-urlencode 'data=[out:json][timeout:25];node(around:20000,40.1,9.0)["emergency"~"water_tank|fire_hydrant|water_source"];out;' https://overpass-api.de/api/interpreter
  ```
  Richiede User-Agent esplicito (senza: HTTP 406). Tag utili: `amenity=fire_station`, `emergency=water_tank`, `emergency=fire_hydrant`, `highway=track`, `natural=spring`. Mirror `overpass.openstreetmap.fr` richiede whitelist, `kumi.systems` ha dato 500.
- Consiglio: precaricare in anticipo punti acqua e caserme in un GeoJSON statico per non dipendere da Overpass durante la demo.

## App esistenti (da cui differenziarsi)
Le descrizioni vengono da risultati di ricerca; lo stato attuale (attive o dismesse) non e verificato salvo dove indicato.

| App | Cosa fa | Limiti / spazio per differenziarsi |
|---|---|---|
| Watch Duty (USA, nonprofit) | Alert incendi in tempo reale, curati da reporter volontari/ex vigili del fuoco, scanner radio, camere, satelliti | Solo USA, segnalazioni filtrate da staff (non crowd aperta), nessuna gamification, nessuna prevenzione |
| FireAware (Fondazione CMCC; nato da NASA Space Apps 2018) | Crowdsensing: segnalazioni georeferenziate di incendi con intensita, in Italia | Progetto accademico, UX/adozione limitate, niente gamification documentata |
| Cittadino Informato (Toscana, ANCI) | Rischio incendio per comune dal bollettino regionale, colori | Solo informativa, nessuna segnalazione/community |
| ABCD (Astroni e Partenio, Campania) | Segnalazioni georeferenziate anche anonime, con risposta | Locale a due aree protette |
| App Regione Sicilia | Segnalazioni foto di criticita varie (incendi inclusi) | Generalista, non specializzata ne gamificata |
| FuelGeoData (Univ. Firenze) | Mappatura del combustibile | Per tecnici, non cittadini |

Spazio libero: nessuna app trovata unisce segnalazione cittadina + dati satellitari + rischio previsto + gamification (punti, badge, squadre per comune/scuola). Esempi di gamification ambientale fuori dominio da citare come ispirazione (non verificati in questa ricerca): iNaturalist (verifica comunitaria delle osservazioni), Forest (Seekrtech), Litterati.

## Raccomandazione per la demo (3 fonti)
1. **EFFIS/GWIS WMS + hotspot FIRMS pubblico** (senza chiave, verificato): mappa con FWI del giorno, hotspot VIIRS ultime 24h filtrati sulla Sardegna e perimetri CFVA storici. Zero registrazioni, il layer FWI da subito impatto visivo ("rischio oggi").
2. **Open-Meteo** (senza chiave, verificato): vento/raffiche, umidita, VPD, giorni senza pioggia per calcolare un indice di rischio proprio per punto o per zona, alimentando alert e le missioni di gamification (es. "giorno ad alto rischio = prevenzione doppia"). Non ha FWI: dirlo in demo e mostrare l'indice come "stima".
3. **Corine Land Cover + OSM** (CLC verificato; OSM da riprovare/estratto): arricchire ogni segnalazione con tipo di vegetazione e vicinanza a strade, punti acqua, caserme. Fa sembrare la segnalazione intelligente, non solo un pin.
- Bonus: FIRMS Area API con MAP_KEY se qualcuno registra la email in anticipo (gratis, 1 minuto) e bollettino PC RAS come PDF mostrato a mano, quando si trova l'URL esatto. Da verificare prima del 16 ottobre: URL bollettino, endpoint geoportale, Overpass.
