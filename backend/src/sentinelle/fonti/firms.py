import csv
import io
from dataclasses import dataclass
from datetime import datetime, timezone

from concurrent.futures import ThreadPoolExecutor

from ..config import DIR_OFFLINE, impostazioni
from .cache import con_cache
from .http import client

URLS = [
    "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Europe_24h.csv",
    "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Europe_24h.csv",
]


@dataclass(frozen=True)
class Hotspot:
    lat: float
    lon: float
    rilevato_il: datetime
    confidenza: str


def _leggi_csv(testo: str) -> list[Hotspot]:
    out = []
    for r in csv.DictReader(io.StringIO(testo)):
        lat, lon = float(r["latitude"]), float(r["longitude"])
        if not (8 <= lon <= 10 and 38.8 <= lat <= 41.3):
            continue
        ora = r["acq_time"].zfill(4)
        quando = datetime.strptime(f"{r['acq_date']} {ora}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
        out.append(Hotspot(lat, lon, quando, r["confidence"]))
    return out


def _scarica() -> list[Hotspot]:
    if impostazioni.modalita_offline:
        return _leggi_csv((DIR_OFFLINE / "firms.csv").read_text())
    with ThreadPoolExecutor(len(URLS)) as pool:
        risposte = list(pool.map(client.get, URLS))
    out = []
    for r in risposte:
        r.raise_for_status()
        out += _leggi_csv(r.text)
    return out


def hotspot_sardegna() -> list[Hotspot] | None:
    """None = fonte non disponibile."""
    return con_cache("firms", _scarica)
