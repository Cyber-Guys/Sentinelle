"""Scarica i dati grezzi in dati/ (WFS Regione Sardegna + istantanea offline). Salta i file presenti."""
import json, math, sys, time
from datetime import date, timedelta
from pathlib import Path
import httpx

DATI = Path(__file__).resolve().parent.parent / "dati"
OFFLINE = DATI / "offline"
WFS = "https://webgis2.regione.sardegna.it/geoserver/dbu/ows"
LAYER_COMUNI = "dbu:limiti_amministr_com_ctr"  # trovato nel GetCapabilities


def get(url, params=None, tentativi=3):
    for i in range(tentativi):
        try:
            r = httpx.get(url, params=params, timeout=120, follow_redirects=True)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  errore ({i + 1}/{tentativi}): {e}", file=sys.stderr)
            time.sleep(5 * (i + 1))
    return None


def wfs(layer, dest):
    if dest.exists():
        print("gia' presente", dest.name)
        return
    print("scarico", layer)
    r = get(WFS, {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer,
                  "outputFormat": "application/json", "srsName": "EPSG:4326"})
    if r is None:
        print("FALLITO", layer, file=sys.stderr)
        return
    dest.write_bytes(r.content)


def offline():
    OFFLINE.mkdir(exist_ok=True)
    f = OFFLINE / "firms.csv"
    if not f.exists():
        r = get("https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Europe_24h.csv")
        if r:
            righe = r.text.splitlines()
            h = righe[0].split(",")
            ilat, ilon = h.index("latitude"), h.index("longitude")
            tenute = [righe[0]] + [l for l in righe[1:] if 8 <= float(l.split(",")[ilon]) <= 10 and 38.8 <= float(l.split(",")[ilat]) <= 41.3]
            f.write_text("\n".join(tenute) + "\n")
    f = OFFLINE / "meteo.json"
    if not f.exists():
        fc = get("https://api.open-meteo.com/v1/forecast", {"latitude": 40.1, "longitude": 9.0, "timezone": "Europe/Rome", "forecast_days": 1,
                 "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m"})
        oggi = date.today()
        ar = get("https://archive-api.open-meteo.com/v1/archive", {"latitude": 40.1, "longitude": 9.0, "timezone": "Europe/Rome",
                 "daily": "precipitation_sum", "start_date": (oggi - timedelta(days=30)).isoformat(), "end_date": (oggi - timedelta(days=1)).isoformat()})
        if fc and ar:
            f.write_text(json.dumps({"forecast": fc.json(), "archivio": ar.json()}))
    f = OFFLINE / "corine.json"
    if not f.exists():
        lon, lat = 9.0, 40.1
        x = lon * 20037508.34 / 180
        y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180) * 20037508.34 / 180
        r = get("https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/identify", {
            "f": "json", "geometry": json.dumps({"x": x, "y": y}), "geometryType": "esriGeometryPoint", "sr": 102100,
            "layers": "all", "tolerance": 1, "mapExtent": f"{x-10000},{y-10000},{x+10000},{y+10000}", "imageDisplay": "400,400,96"})
        if r:
            f.write_text(r.text)


if __name__ == "__main__":
    DATI.mkdir(exist_ok=True)
    for anno in range(2005, 2026):
        wfs(f"dbu:areeincendiateperim{anno}", DATI / f"perimetri_{anno}.geojson")
    wfs("dbu:exp_pericolo_23", DATI / "pericolo_aib.geojson")
    wfs(LAYER_COMUNI, DATI / "comuni.geojson")
    offline()
    for p in sorted(DATI.rglob("*")):
        if p.is_file():
            n = ""
            if p.suffix == ".geojson":
                n = f"{len(json.loads(p.read_text())['features'])} feature"
            print(f"{p.relative_to(DATI)}\t{p.stat().st_size // 1024} KB\t{n}")
