import json
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from concurrent.futures import ThreadPoolExecutor

from ..config import DIR_OFFLINE, impostazioni
from .cache import con_cache
from .http import client

CELLA = 0.05


@dataclass(frozen=True)
class Meteo:
    vento_kmh: float
    raffiche_kmh: float
    umidita: float
    temperatura: float
    giorni_senza_pioggia: int


def _costruisci(forecast: dict, archivio: dict) -> Meteo:
    h = forecast["hourly"]
    ora = datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y-%m-%dT%H:00")
    i = h["time"].index(ora) if ora in h["time"] else 0
    giorni = 0
    for mm in reversed(archivio["daily"]["precipitation_sum"]):
        if mm is None or mm >= 1:
            break
        giorni += 1
    return Meteo(h["wind_speed_10m"][i], h["wind_gusts_10m"][i],
                 h["relative_humidity_2m"][i], h["temperature_2m"][i], giorni)


def _scarica(lat: float, lon: float) -> Meteo:
    if impostazioni.modalita_offline:
        d = json.loads((DIR_OFFLINE / "meteo.json").read_text())
        return _costruisci(d["forecast"], d["archivio"])
    with ThreadPoolExecutor(2) as pool:  # forecast e archivio in parallelo
        f = pool.submit(client.get, "https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon, "forecast_days": 1, "timezone": "Europe/Rome",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m"})
        a = pool.submit(client.get, "https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": lat, "longitude": lon, "daily": "precipitation_sum", "timezone": "Europe/Rome",
            "past_days": 30, "forecast_days": 1})
        f, a = f.result(), a.result()
    f.raise_for_status()
    a.raise_for_status()
    return _costruisci(f.json(), a.json())


def meteo(lat: float, lon: float) -> Meteo | None:
    # cella di 0,05 gradi (~5 km): il meteo e' interrogato al centro cella, punti vicini condividono la cache
    ci, cj = round(lat / CELLA), round(lon / CELLA)
    return con_cache(f"meteo:{ci}:{cj}", lambda: _scarica(ci * CELLA, cj * CELLA))
