"""Rischio di oggi per cella ~2 km: storico + pericolo AIB + meteo peggiore delle prossime 24 h."""
import math
import tomllib

from sqlalchemy import text

from .config import FILE_PESI
from .db import engine
from .fonti.meteo import Meteo
from .fonti.meteo_orario import Serie, previsione, serie_vicina
from .rischio import rischio_meteo

DLAT, DLON = 0.02, 0.025
PESI = tomllib.loads(FILE_PESI.read_text())["rischio_oggi"]


def meteo_peggiore(s: Serie) -> float:
    return max((rischio_meteo(Meteo(o.vento_kmh, o.raffiche_kmh, o.umidita, o.temperatura, s.giorni_senza_pioggia))
                for o in s.ore[:24]), default=0.0)


def griglia() -> dict:
    p = previsione()
    rm = {(s.lat, s.lon): meteo_peggiore(s) for s in p.serie}
    with engine.connect() as c:
        righe = c.execute(text("SELECT lon, lat, storico, pericolo FROM cella")).all()
    smax = math.log1p(max((r.storico for r in righe), default=1) or 1)
    celle = []
    for r in righe:
        s = serie_vicina(p, r.lat, r.lon)
        v = (PESI["storico"] * math.log1p(r.storico) / smax + PESI["pericolo"] * r.pericolo
             + PESI["meteo"] * rm[(s.lat, s.lon)])
        celle.append([round(r.lon, 4), round(r.lat, 4), round(v, 3)])
    return {"celle": celle, "aggiornato_il": p.inizio, "meteo_simulato": p.simulato}
