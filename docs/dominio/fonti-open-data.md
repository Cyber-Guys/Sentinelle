# Fonti open data: SardegnaSIRA e dati.gov.it

Verifica del 2026-10-09, chiamate reali eseguite da curl (nessun account, nessuna credenziale).
Legenda: [OK] verificato con chiamata reale; [NV] non verificabile / non risponde.

Sintesi: il portale SardegnaSIRA e' una vetrina di pagine con mappe/form (Liferay + SardegnaMappe), NON espone API JSON documentate. I dati scaricabili veri stanno altrove: ARPAS (CSV, catalogati su dati.gov.it) e Geoportale RAS (WFS/WMS). dati.gov.it ha CKAN API funzionante.

---

## 1. SardegnaSIRA - https://portal.sardegnasira.it/dati-ambientali

### Contenuto
Hub con 10 aree tematiche, ognuna una pagina `/web/sardegnaambiente/<slug>` quasi sempre con mappa embedded e form di ricerca:

| Area | Cosa c'e' davvero |
|---|---|
| Aria | Mappa stazioni qualita' aria (`/mappa-stazioni-misura`), ricerca stazioni (`/ricerca-stazioni-di-misura`, filtri zona/provincia/comune), report e indicatori, inventario emissioni (solo anni 2001 e 2010), tabella anagrafica inquinanti |
| Acque | Pagina con mappe (balneazione, corpi idrici) |
| Natura e biodiversita' | Natura 2000, parchi e aree protette, grotte, fauna e attivita' venatoria |
| Suolo e siti contaminati | Siti contaminati, difesa del suolo |
| Rifiuti | Rifiuti urbani, rifiuti speciali (mappa) |
| Cambiamenti climatici | Clima e indicatori (`/clima`), scenari climatici, pericoli climatici (`/pericolo`) |
| Energia, Agenti fisici, AIA e RIR, Sostenibilita' | Pagine informative/mappe |
| Rete meteo | `/rete-meteo-climatica-dati-ambientali`: Rete Unica regionale, 186 stazioni meteo e termopluviometriche, form di ricerca per stazione/provincia/comune, scheda PDF stazioni |
| Navigatore cartografico | `/cartografico` (SardegnaMappe) |

### Formati e accesso
- HTML + viewer SardegnaMappe (`https://portal.sardegnasira.it/sardegnamappe/?map=ms72k_qualita_aria&framemode=1` [OK] 200) e form di ricerca. Nessun link diretto a CSV/JSON nelle pagine analizzate.
- Unico file statico trovato: PDF scheda stazioni Rete Unica `https://portal.sardegnasira.it/documents/21213/200223/Rete_Unica-scheda+stazioni.pdf/9bbf3d0f-1d98-46e8-a5b3-71a5b843b9ed` [OK] 200, 128 KB.
- Estrazione dati meteo realtime: solo tramite form web (non scriptabile in modo stabile; richiede scraping di portlet Liferay, da evitare).

### API / servizi OGC
- API JSON documentata: **non trovata** (nessun endpoint in pagina). `/geoserver/ows` su portal.sardegnasira.it risponde 404 [OK, negativo].
- Servizi OGC: non sul portale SIRA, ma sul Geoportale RAS (vedi sezione 3): WFS e WMS ufficiali.

### Frequenza, licenza, qualita'
- Frequenza: realtime per aria e rete meteo (dati "non validati", marca temporale UTC; i validati vanno chiesti ad ARPAS). Inventario emissioni fermo al 2010. Altre sezioni senza data dichiarata.
- Licenza: pagine con link **CC BY-NC-ND 4.0** (non commerciale, no opere derivate) nelle pagine aria e rete meteo. Attenzione: incompatibile con riuso/derivazione libera; per l'hackathon chiedere conferma agli organizzatori o preferire ARPAS (CC BY 4.0).
- Qualita': contenuti eterogenei, molta documentazione e poca fruibilita' machine-readable. Link rotti: nessuno sui link interni verificati (tutti 200). Il link "staging" del cartografico (`/web/sardegnaambiente-staging/cartografico`) e' un residuo tecnico; `sardegnamappe?map=ms72k_rete_unica_regionale_test` ha "test" nel nome.
- Limiti: niente bulk download, niente storico API, dipendenza da form e mappe.

---

## 2. dati.gov.it - https://www.dati.gov.it/view-dataset

### Contenuto
Catalogo nazionale CKAN che raccoglie (harvest) altri cataloghi. Per la Sardegna (ricerca `sardegna`: 577 dataset, [OK]):
- **ARPAS** (13 dataset): meteo-clima e idrologia, vedi tabella sotto.
- **GeoDati-RNDT** (433 dataset): metadati di dati territoriali RAS, inclusi incendi (25 dataset: aree percorse dal fuoco CFVA 2005-2021 e oltre, zone allerta PRAI 2016, carta rischio e pericolo incendio 2017, danno potenziale/ambientale PRPP), rifiuti (catasto impianti, produzione RSU/speciali), qualita' aria agglomerato Cagliari, zone allerta idrogeologica.
- Laore Sardegna (12, agricoltura), ASPAL (15, lavoro), altri minori.

Dataset ARPAS principali (formato CSV salvo nota):

| Dataset | Periodo / aggiornamento | URL esempio |
|---|---|---|
| Misure climatiche reti agro-meteo-pluvioclimatologiche da gennaio 2026 (temperatura, precipitazioni, vento; file trimestrali RF e RUR) | pubblicato a trimestre; Q1 e Q2 2026 online, catalogo aggiornato 2026-09-30 | `https://dati.arpasambiente.it/meteo/dsm/dati_rf_da_04_a_06_2026.csv` |
| Misure climatiche storiche 1981-2020 | storico (CSV + ZIP) | `https://dati.arpasambiente.it/meteo/dsm/1991-2020.zip` |
| Temperature aria (TCI) | annuale, 1995-2025, frequenza MONTHLY dichiarata | `https://dati.arpasambiente.it/meteo/Temperature/TCI_2025.csv` |
| Altezze di pioggia (P1H) | annuale, 2023-2025 | `.../meteo/Pioggia/P1H_2025.csv` |
| Umidita' relativa (UCI) | annuale | `.../meteo/Umidita/UCI_2025.csv` |
| Vento 10 m intensita' (VAI) e direzione (DVI) | annuale | `.../meteo/Vento10m/VAI_2025.csv`, `.../meteo/DirezioneVento10m/DVI_2025.csv` |
| Radiazione globale (RGI) | annuale | `.../meteo/RadiazioneGlobale/RGI_2025.csv` |
| Livelli idrometrici (LIT), portate (QIT) | annuale | `.../idro/LIT/LIT_2025.csv` |
| Monitoraggio pollini 2007-2025 | CSV + JSON | `.../pollini/Dati_Aerobio_2025.json` |
| Rifiuti: raccolta differenziata per tipologia, costo servizio | annuale per comune, 2021-2024 | `.../rifiuti/Pubblicazione_Rifiuti_urbani_2024.csv` |

Anagrafiche: `.../meteo/Temperature/anagrafica_stazioni_TCI.csv` (coordinate UTM 32N EPSG:32632, quota, rete, sensori disponibili), `.../meteo/dsm/anagrafica_grandezze.csv` (codici grandezza).

### Formati
CSV dominante (130 risorse su 577 nel set Sardegna), XML 61, PDF 45, JSON 21, XLSX 15, ZIP 23. Gli ARPAS sono CSV puri; i metadati RNDT spesso NON hanno URL diretto di risorsa (campo `url` vuoto): il file vero e' nell'extra `landingpage` (es. ZIP shapefile su webgis.regione.sardegna.it, 11 MB [OK]).

### API CKAN (funzionante) [OK]
Base: `https://www.dati.gov.it/opendata/api/3/action/` (NB: `/api/3/action` senza `/opendata` risponde 404; `/sparql` 404).

Esempio testato (HTTP 200, 4 risultati):
```
curl -sG "https://www.dati.gov.it/opendata/api/3/action/package_search" \
  --data-urlencode "q=sardegna meteo" --data-urlencode "rows=10"
```
Altre chiamate testate:
- Tutti i dataset ARPAS: `package_search?fq=organization:agenzia-regionale-per-la-protezione-dell-ambiente-della-sardegna&rows=30` (13)
- Incendi: `package_search?q=incendi sardegna&rows=25` (25)
- Facet: `package_search?q=sardegna&rows=0&facet.field=["organization","res_format","license_id"]`
- `organization_list?all_fields=true&limit=1000` [OK]
Note: gli ID in `package_show` sono hash lunghi (64 car.); `package_show?id=<hash completo>` funziona, quelli troncati danno 404 "Non trovato". Meglio usare `package_search`. L'URL del portale `https://www.dati.gov.it/view-dataset/dataset?id=<hash>` e' la pagina HTML.

### Licenza
- ARPAS: campo `license_id` del dataset vuoto, ma ogni risorsa riporta `https://creativecommons.org/licenses/by/4.0/` (**CC BY 4.0**). Da leggere a livello risorsa.
- RNDT/RAS: CC BY 4.0 (498 su 577 dataset Sardegna, il resto cc-by/CC0).

### Frequenza e qualita'
- ARPAS meteo: aggiornamento trimestrale/annuale con ritardo (file 2025 caricati a marzo 2026, trimestri 2026 a fine settembre). **Non e' realtime.**
- Dimensioni notevoli: `dati_rf_da_01_a_03_2026.csv` 282 MB, `TCI_2025.csv` 95 MB, `VAI_2025.csv` 17 MB: servono streaming/chunk o pre-aggregazione.
- Formati eterogenei: file annuali `cod_staz,data_mis,valore,liv_validaz` (virgola, date ISO UTC, `liv_validaz`) vs trimestrali `NOME;COD_STAZ;COD_GRAND;DATA_MIS;VALORE;PERIODO_ARC` (punto e virgola, data `ddmmyyyyHHMM`, decimale con virgola, es. `,2`). Anagrafiche con BOM e `;`.
- RNDT: metadati vecchi (es. rischio incendio 2017, `modified` 2017) anche se harvest recente (2026-09-19). Nessuna risorsa WMS/WFS esposta nel catalogo (ricerca `res_format:(WMS OR WFS)` = 0).
- Link rotti: nessuno sui file ARPAS testati (tutti 200). `https://dati.arpasambiente.it/` (root) -> AccessDenied (solo bucket, normale). Alcuni dataset RNDT hanno risorse senza URL.

---

## 3. Servizi OGC Geoportale RAS (trovati seguendo i link; non sono SIRA ma sono la fonte vera dei dati geo)

Pagine ufficiali: https://www.sardegnageoportale.it/ -> "Consulta i dati con il WMS" / "Scarica i dati con il WFS".
- Endpoint ufficiali dichiarati: `https://webgis.regione.sardegna.it/geoserver/ows?service=WMS|WFS&request=GetCapabilities` e `.../geoserverraster/ows` per i raster. [NV] da questa rete: timeout a 100-150 s.
- Endpoint alternativo **funzionante**: `https://webgis2.regione.sardegna.it/geoserver/ows`
  - WFS GetCapabilities [OK] 200 in ~4 s, WFS 2.0.0, 359 feature types, output `application/json`, `csv`, `SHAPE-ZIP`, `json`; Fees/AccessConstraints = NONE. 
  - WMS su webgis2: [NV] timeout.
- Layer rilevanti (prefisso `dbu:`): `areeincendiateperim2005`..`areeincendiateperim2025` (perimetri aree percorse dal fuoco CFVA), `areeincendiatetipol2005`..`2025` (tipologie soprassuolo), `pericoloincendioboschivo_2017`, `rischioincendioboschivo_2017`, `zoneallertaincendiprai2016`, `qualita_aria_agglom_cagliari`, `zoneallertaidrogeologica`, `dbgt_10k_22_v05_*` (DBGT 10k: viabilita', vegetazione).
- Chiamata testata [OK] (HTTP 200, ma **78 s** per 2 feature; capacita' lenta, usare `count`, `cql_filter`, caching):
```
curl "https://webgis2.regione.sardegna.it/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=dbu:areeincendiateperim2025&outputFormat=application/json&count=2&srsName=EPSG:4326"
```
  Risultato: `numberMatched` = 1362 incendi 2025; campi `cod_incend` (es. 2025/CA/0005), `stir`, `data` (dd/mm/yyyy), `stazione`, `prov`, `comune`, `toponimo`, `tipologia`, `bosco_mq`, `pascolo_mq`, `altro_mq`, `totale_ha`, `bbox`, geometria MultiPolygon.
- Attenzione CRS: senza `srsName` la geometria esce in metri (es. EPSG:7791 / UTM) invece di WGS84, vedi `zoneallertaincendiprai2016`.
- Scarico bulk alternativo: ZIP shapefile (es. `https://webgis.regione.sardegna.it/scaricocartografiaETL/protezioneCivile/rischio_incendio_boschivo_2017.zip` [OK] 200, 11,9 MB, CC BY 4.0).

---

## Utilita' per challenge 1 e 5

**Challenge 1 (dashboard che integra DB ambientali frammentati)**
- Prima scelta come dati veri: ARPAS CSV (meteo, idro, pollini, rifiuti per comune) + WFS Geoportale (aree incendiate, rischio, qualita' aria Cagliari). Tutti CC BY 4.0, scaricabili senza account.
- SIRA come "frammentazione dimostrabile": 10 aree tematiche, ognuna con mappa/form propria e nessuna API; il valore sta nel catalogare e unificare, e nel mostrare il gap con la lista dei dataset.
- Chiave di integrazione: codice stazione (`COD_STAZ`) + coordinate UTM 32N (anagrafiche) e codice comune (rifiuti, incendi: campo `comune`).
- Per qualita' aria vera: SIRA offre solo form/mappa; per Cagliari esiste il layer WFS `qualita_aria_agglom_cagliari` (probabilmente statico/zonizzazione, da verificare nei campi).

**Challenge 5 (portale con API semplificate)**
- Il gap e' reale e dimostrato: nessuna API JSON su SIRA; CSV ARPAS enormi con due schemi diversi; WFS lento (78 s) e con CRS non WGS84 di default.
- Proposta tecnica: ETL che scarica/normalizza i CSV (unificando i due schemi, date UTC ISO, decimali) in Postgres/Parquet e li serve via FastAPI con endpoint `/stazioni`, `/misure?cod_staz=&da=&a=`, `/incendi?anno=&comune=` (GeoJSON in WGS84), con cache dei layer WFS.
- Usare CKAN `package_search` come registro dinamico dei dataset (nuove release trimestrali ARPAS) invece di URL hardcoded.

## Utilita' trasversale per le challenge incendi

Indice di rischio incendio (stile FWI semplificato) costruibile solo con fonti aperte verificate:
- **Meteo ARPAS**: temperatura (TCI), umidita' relativa (UCI), vento intensita' (VAI) e direzione (DVI), pioggia (P1H) -> giorni dall'ultima pioggia, temperatura alta + umidita' bassa + vento forte. Granularita' oraria/10 min per stazione; limite: ritardo di mesi, quindi addestramento su storico, non nowcasting. Per il realtime servirebbe altra fonte (SIRA rete unica non validata via form, oppure Open-Meteo/ERA5 esterni, da valutare).
- **Verita' a terra**: WFS `areeincendiateperim2005..2025` (21 anni di perimetri con data, comune, ettari, tipologia) come etichette per addestrare/validare il modello; 1362 eventi nel solo 2025.
- **Rischio statico**: `rischioincendioboschivo_2017`, `pericoloincendioboschivo_2017`, `zoneallertaincendiprai2016` (zone di allerta PRAI) come feature di base e baseline di confronto; `dbgt_10k_22` per viabilita' e vegetazione (accessibilita' mezzi).
- **Qualita' dell'aria**: utile in post-evento (PM10/PM2.5 e CO da fumi) per stimare impatto, ma i dati SIRA sono solo via form/mappa; sul WFS c'e' solo il layer Cagliari. Priorita' bassa.
- **Pollini/umidita'/radiazione**: radiazione globale (RGI) e umidita' aiutano a stimare secchezza del combustibile vegetale.
- Join spaziale: stazioni ARPAS (UTM 32N, riproiettare in 4326) -> incendio piu' vicino per data/comune, per costruire dataset `(meteo giorno X, stazione vicina) -> incendio si/no`.

## Prossimi passi consigliati
1. Scaricare anagrafica stazioni + TCI/UCI/VAI/P1H 2023-2025 e normalizzare (stream per i file grandi).
2. Scaricare in blocco `areeincendiateperim20xx` come GeoJSON (con `srsName=EPSG:4326`) una volta sola, cache locale; provare anche `webgis.regione.sardegna.it` da altra rete.
3. Chiedere agli organizzatori: licenza effettiva dei dati SIRA (CC BY-NC-ND) e se esiste accesso ai dati realtime.
