"""Previsione oraria Open-Meteo su una griglia grossa (0,25 gradi) della Sardegna: una sola chiamata, cache 1 h.
Offline o rete giu': meteo costante plausibile (maestrale), dichiarato con simulato=True."""
import time
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from ..config import impostazioni
from .cache import con_cache
from .http import client

PASSO = 0.25
PUNTI = [(39.0 + i * PASSO, 8.25 + j * PASSO) for i in range(10) for j in range(7)]  # 70 punti
ORE = 30


@dataclass(frozen=True)
class Ora:
    vento_kmh: float
    da_gradi: float      # direzione DA cui soffia (convenzione meteo)
    umidita: float
    pioggia_mm: float
    temperatura: float
    raffiche_kmh: float


@dataclass(frozen=True)
class Serie:
    lat: float
    lon: float
    ore: list[Ora]       # dall'ora corrente in avanti
    giorni_senza_pioggia: int


@dataclass(frozen=True)
class Previsione:
    inizio: str          # ISO dell'ora corrente
    serie: list[Serie]
    simulato: bool


def _ora_corrente() -> datetime:
    return datetime.now(ZoneInfo("Europe/Rome")).replace(minute=0, second=0, microsecond=0)


def _costante() -> Previsione:
    o = Ora(25.0, 300.0, 30.0, 0.0, 31.0, 40.0)
    return Previsione(_ora_corrente().isoformat(), [Serie(la, lo, [o] * ORE, 10) for la, lo in PUNTI], True)


def _scarica() -> Previsione:
    r = client.get("https://api.open-meteo.com/v1/forecast", timeout=6, params={
        "latitude": ",".join(f"{p[0]:.2f}" for p in PUNTI), "longitude": ",".join(f"{p[1]:.2f}" for p in PUNTI),
        "hourly": "wind_speed_10m,wind_direction_10m,relative_humidity_2m,precipitation,temperature_2m,wind_gusts_10m",
        "forecast_days": 2, "past_days": 14, "timezone": "Europe/Rome"})
    r.raise_for_status()
    dati = r.json()
    dati = dati if isinstance(dati, list) else [dati]
    adesso = _ora_corrente()
    chiave = adesso.strftime("%Y-%m-%dT%H:00")
    serie = []
    for (la, lo), d in zip(PUNTI, dati):
        h = d["hourly"]
        i = h["time"].index(chiave) if chiave in h["time"] else 0
        ore = [Ora(h["wind_speed_10m"][k] or 0, h["wind_direction_10m"][k] or 0, h["relative_humidity_2m"][k] or 50,
                   h["precipitation"][k] or 0, h["temperature_2m"][k] or 20, h["wind_gusts_10m"][k] or 0)
               for k in range(i, min(i + ORE, len(h["time"])))]
        # giorni senza pioggia: a ritroso dall'ora corrente, a blocchi di 24 h
        giorni, k = 0, i
        while k >= 24 and sum(v or 0 for v in h["precipitation"][k - 24:k]) < 1:
            giorni, k = giorni + 1, k - 24
        serie.append(Serie(la, lo, ore, giorni))
    return Previsione(adesso.isoformat(), serie, False)


_fallito_il = 0.0


def previsione() -> Previsione:
    """Rete giu': per 5 minuti non si riprova, cosi' le richieste non aspettano il timeout a ogni chiamata."""
    global _fallito_il
    if impostazioni.modalita_offline or time.time() - _fallito_il < 300:
        return _costante()
    p = con_cache("meteo_orario", _scarica, durata_s=3600)
    if p is None:
        _fallito_il = time.time()
    return p or _costante()


def serie_vicina(p: Previsione, lat: float, lon: float) -> Serie:
    return min(p.serie, key=lambda s: (s.lat - lat) ** 2 + (s.lon - lon) ** 2)
