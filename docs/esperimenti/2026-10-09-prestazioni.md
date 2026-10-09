# Prestazioni: PostGIS nativo, fonti esterne in parallelo, tile dello storico

Macchina: Apple Silicon, Docker Desktop. Misure del 2026-10-09 (rete reale, Open-Meteo/Corine/FIRMS).

| Misura | Prima | Dopo |
|---|---|---|
| Query vicinanza `incendio_storico` (9.05,40.05, 1000 m), EXPLAIN ANALYZE | 59,7 ms (amd64 emulato) | 7,4-8,6 ms (arm64 nativo) |
| `POST /segnalazioni` a freddo (punti casuali, meteo/Corine non in cache) | 0,93-1,06 s (un outlier 5,6 s di rete) | 0,21-0,34 s (prima chiamata del processo 1,1 s: connessioni e FIRMS freddi) |
| `GET /rischio` a freddo | 510 ms (1,2 s a processo freddo) | 63-68 ms |
| `GET /rischio` a caldo | 10-14 ms | 8-17 ms |
| `/storico/incendi` | troncato in silenzio a 2000 | risponde con `"troncato": true` oltre 2000 |
| `/storico/statistiche?comune=` | non esisteva | incendi ed ettari per anno in SQL, senza geometrie |
| `storico.pmtiles` | non esisteva | 20,4 MB, zoom 6-14, 27544 feature, layer `incendi` |

## Cosa e' cambiato

- `infra/compose.yaml`: `imresamu/postgis:17-3.5` senza `platform` (multi-arch). Volume ricreato.
- `fonti/http.py`: `httpx.Client` condiviso (keep-alive). Meteo e Corine usano `client.get`.
- Meteo: cache per cella di 0,05 gradi (~5 km), TTL 10 min, interrogato al centro cella; forecast e archive in parallelo.
- Corine: resta sul punto, cache a 4 decimali.
- `verifica.raccogli_contesto`: meteo, Corine e hotspot in parallelo (ThreadPoolExecutor) mentre il thread fa le query DB. FIRMS: i due CSV in parallelo.
- `scripts/campi_incendi.py`: mappatura campi condivisa da `carica_dati.py` e `genera_tiles.py`.
- `scripts/carica_dati.py`: corretto lo split di `schema.sql` su `-- gioco:` (lasciava testo del commento e dava SyntaxError su DB nuovo).

## Tile (tippecanoe v2.79.0)

`-l incendi -zg --minimum-zoom=6 --drop-densest-as-needed --extend-zooms-if-still-dropping`. A zoom bassi cadono solo i `tiny_polygons`
(i piccoli spariscono, i grandi restano); a z6 restano ~11,5k feature, a z7 ~43k (conteggio con ritagli per tile).
Proprieta': `anno` (int), `data` ("AAAA-MM-GG", assente se nulla), `comune`, `ettari`, `bosco_ha` (assenti se nulli).

## Comandi

```bash
# bench: 5 POST /segnalazioni area_a_rischio (utente 1, punti casuali 39.9-40.4 N, 8.8-9.4 E), poi /rischio freddo e 3 caldi
curl -s -X POST localhost:8000/segnalazioni -F utente_id=1 -F tipo=area_a_rischio -F lat=40.1 -F lon=9.0
curl -s "localhost:8000/rischio?lat=40.1&lon=9.0"
# query di vicinanza
docker exec -i infra-db-1 psql -U sentinelle -c "EXPLAIN ANALYZE SELECT count(*) FROM incendio_storico WHERE geom && ST_Expand(ST_SetSRID(ST_MakePoint(9.05,40.05),4326),0.05) AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(9.05,40.05),4326)::geography, 1000) AND anno BETWEEN 2005 AND 2025"
# ricreare il DB
docker compose -f infra/compose.yaml down -v && docker compose -f infra/compose.yaml up -d
python scripts/carica_dati.py && python scripts/semina_demo.py
# tile e ispezione
python scripts/genera_tiles.py
pmtiles-show frontend/public/tiles/storico.pmtiles
tippecanoe-decode frontend/public/tiles/storico.pmtiles 7 67 48
```

Nota: `brew install tippecanoe` e' bloccato finche' la licenza Xcode non e' accettata (`sudo xcodebuild -license accept`);
in questa sessione tippecanoe e `pmtiles` sono stati installati da conda-forge (`conda create -n tiles -c conda-forge tippecanoe pmtiles`).
