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
    frp: float | None = None
    luminosita: float | None = None
    satellite: str | None = None
    giorno: bool | None = None


SATELLITI = {"N": "Suomi NPP", "1": "NOAA-20", "N20": "NOAA-20"}


def _num(v: str | None) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def _leggi_csv(testo: str, url: str = "") -> list[Hotspot]:
    dedotto = "Suomi NPP" if "suomi" in url.lower() else "NOAA-20" if "noaa-20" in url.lower() else None
    out = []
    for r in csv.DictReader(io.StringIO(testo)):
        lat, lon = float(r["latitude"]), float(r["longitude"])
        if not (8 <= lon <= 10 and 38.8 <= lat <= 41.3):
            continue
        ora = r["acq_time"].zfill(4)
        quando = datetime.strptime(f"{r['acq_date']} {ora}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
        dn = r.get("daynight")
        out.append(Hotspot(lat, lon, quando, r["confidence"], _num(r.get("frp")), _num(r.get("bright_ti4")),
                           SATELLITI.get((r.get("satellite") or "").strip().upper()) or dedotto,
                           dn == "D" if dn in ("D", "N") else None))
    return out


def _scarica() -> list[Hotspot]:
    if impostazioni.modalita_offline:
        return _leggi_csv((DIR_OFFLINE / "firms.csv").read_text())
    with ThreadPoolExecutor(len(URLS)) as pool:
        risposte = list(pool.map(client.get, URLS))
    out = []
    for u, r in zip(URLS, risposte):
        r.raise_for_status()
        out += _leggi_csv(r.text, u)
    return out


def hotspot_sardegna() -> list[Hotspot] | None:
    """None = fonte non disponibile."""
    return con_cache("firms", _scarica)
