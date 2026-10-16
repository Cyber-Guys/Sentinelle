"""Aree critiche di oggi: celle a rischio alto raggruppate per contiguita', con motivi, picco orario e invaso vicino."""
import json
import math
import re

from sqlalchemy import text

from .db import engine
from .fonti.cache import con_cache
from .fonti.meteo import Meteo
from .fonti.meteo_orario import previsione, serie_vicina
from .rischio import rischio_meteo
from .rischio_oggi import PESI, meteo_peggiore

SOGLIA_ALTO, SOGLIA_MOLTO_ALTO = 0.6, 0.7
MAX_CELLE = 100      # con giornate molto secche si alza la soglia: zone mirate, non mezza isola
MAX_AREE = 8


def raggruppa(celle: list[dict]) -> list[list[dict]]:
    """Componenti connesse (8 vicini sulla griglia i,j). Zone di una sola cella solo se molto alto."""
    per_ij = {(c["i"], c["j"]): c for c in celle}
    visti, gruppi = set(), []
    for c in sorted(celle, key=lambda c: -c["valore"]):
        k = (c["i"], c["j"])
        if k in visti:
            continue
        visti.add(k)
        gruppo, coda = [], [k]
        while coda:
            ci, cj = coda.pop()
            gruppo.append(per_ij[(ci, cj)])
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    v = (ci + di, cj + dj)
                    if v in per_ij and v not in visti:
                        visti.add(v)
                        coda.append(v)
        if len(gruppo) > 1 or gruppo[0]["valore"] >= SOGLIA_MOLTO_ALTO:
            gruppi.append(gruppo)
    return sorted(gruppi, key=lambda g: -max(c["valore"] for c in g))


def picco(ore) -> dict:
    """Finestra contigua attorno all'ora peggiore con rischio meteo entro il 90% del massimo (prime 24 h)."""
    r = [rischio_meteo(Meteo(o.vento_kmh, o.raffiche_kmh, o.umidita, o.temperatura, 0)) for o in ore[:24]]
    if not r:
        return {"i": 0, "f": 0}
    m = max(range(len(r)), key=lambda k: r[k])
    a = b = m
    while a > 0 and r[a - 1] >= 0.9 * r[m]:
        a -= 1
    while b < len(r) - 1 and r[b + 1] >= 0.9 * r[m]:
        b += 1
    return {"i": a, "f": b + 1}


ACCENTI = str.maketrans("aeiou", "àèìòù")


def _accenta(nome: str) -> str:
    """Grafia catastale con apostrofo al posto dell'accento: "Senorbi'" -> "Senorbì"."""
    return re.sub(r"([aeiou])'(?=\s|$)", lambda m: m.group(1).translate(ACCENTI), nome)


def _nome(comuni: list[str]) -> str:
    if not comuni:
        return "zona senza comune"
    if len(comuni) == 1:
        return f"a {comuni[0]}"
    e = "ed" if comuni[1][:1] in "EÈ" else "e"
    return f"tra {comuni[0]} {e} {comuni[1]}"


def _calcola() -> dict:
    p = previsione()
    rm = {(s.lat, s.lon): meteo_peggiore(s) for s in p.serie}
    with engine.connect() as c:
        righe = c.execute(text("SELECT id, i, j, lon, lat, storico, pericolo FROM cella")).all()
        smax = math.log1p(max((r.storico for r in righe), default=1) or 1)
        celle = []
        for r in righe:
            s = serie_vicina(p, r.lat, r.lon)
            v = (PESI["storico"] * math.log1p(r.storico) / smax + PESI["pericolo"] * r.pericolo
                 + PESI["meteo"] * rm[(s.lat, s.lon)])
            celle.append({"id": r.id, "i": r.i, "j": r.j, "lon": r.lon, "lat": r.lat, "valore": round(v, 3),
                          "storico": math.log1p(r.storico) / smax, "pericolo": r.pericolo})
        valori = sorted((x["valore"] for x in celle), reverse=True)
        soglia = max(SOGLIA_ALTO, valori[MAX_CELLE] if len(valori) > MAX_CELLE else 0)
        gruppi = raggruppa([x for x in celle if x["valore"] > soglia])[:MAX_AREE]
        inizio = int(p.inizio[11:13])
        aree = []
        for n, g in enumerate(gruppi):
            peggiore = max(g, key=lambda x: x["valore"])
            ids = [x["id"] for x in g]
            geo = c.execute(text(
                "WITH u AS (SELECT ST_Union(geom) g FROM cella WHERE id = ANY(:ids)) "
                "SELECT ST_AsGeoJSON(ST_SimplifyPreserveTopology(u.g, 0.001), 5) area, "
                "ST_X(ST_Centroid(u.g)) lon, ST_Y(ST_Centroid(u.g)) lat, "
                "(SELECT array_agg(initcap(lower(nome)) ORDER BY a DESC) FROM (SELECT co.nome, "
                "  ST_Area(ST_Intersection(co.geom, u.g)) a FROM comune co WHERE ST_Intersects(co.geom, u.g)) x) comuni, "
                "(SELECT count(*) FROM incendio_storico f WHERE f.anno >= 2005 AND ST_Intersects(f.geom_semplice, u.g)) incendi "
                "FROM u"), {"ids": ids}).one()
            inv = c.execute(text(
                "SELECT nome, riempimento, ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) d "
                "FROM invaso ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) LIMIT 1"),
                {"lon": geo.lon, "lat": geo.lat}).one_or_none()
            s = serie_vicina(p, peggiore["lat"], peggiore["lon"])
            ore = s.ore[:24]
            raffiche = max((o.raffiche_kmh for o in ore), default=0)
            umidita = min((o.umidita for o in ore), default=50)
            temp = max((o.temperatura for o in ore), default=20)
            pk = picco(ore)
            dalle, alle = f"{(inizio + pk['i']) % 24:02d}:00", f"{(inizio + pk['f']) % 24:02d}:00"
            motivo = [f"raffiche fino a {raffiche:.0f} km/h", f"umidità minima {umidita:.0f}%",
                      f"temperatura massima {temp:.0f} °C"]
            if s.giorni_senza_pioggia >= 3:
                motivo.append(f"{s.giorni_senza_pioggia} giorni senza pioggia")
            if geo.incendi:
                motivo.append(f"{geo.incendi} {'incendio registrato' if geo.incendi == 1 else 'incendi registrati'} nell'area dal 2005")
            if peggiore["pericolo"] >= 0.75:
                motivo.append("vegetazione a pericolo AIB alto")
            testo = ", ".join(motivo)
            comuni = [_accenta(x) for x in geo.comuni or []]
            aree.append({
                "id": n + 1,
                "livello": "molto_alto" if peggiore["valore"] >= SOGLIA_MOLTO_ALTO else "alto",
                "indice": peggiore["valore"],
                "centro": {"lat": round(geo.lat, 5), "lon": round(geo.lon, 5)},
                "area": json.loads(geo.area),
                "comuni": comuni,
                "nome": _nome(comuni),
                "motivo": testo[0].upper() + testo[1:] + ".",
                "picco": {"dalle": dalle, "alle": alle},
                "fattori": [
                    {"chiave": "storico", "etichetta": "Storico incendi", "valore": round(peggiore["storico"], 2),
                     "testo": f"{geo.incendi} incendi registrati nell'area dal 2005"},
                    {"chiave": "pericolo", "etichetta": "Pericolo vegetazione", "valore": round(peggiore["pericolo"], 2),
                     "testo": "Carta del pericolo AIB regionale"},
                    {"chiave": "vento", "etichetta": "Vento", "valore": round(min(1, raffiche / 60), 2),
                     "testo": f"Raffiche fino a {raffiche:.0f} km/h"},
                    {"chiave": "umidita", "etichetta": "Aria secca", "valore": round(min(1, max(0, (100 - umidita) / 70)), 2),
                     "testo": f"Umidità minima {umidita:.0f}%"},
                    {"chiave": "pioggia", "etichetta": "Siccità", "valore": round(min(1, s.giorni_senza_pioggia / 15), 2),
                     "testo": f"{s.giorni_senza_pioggia} giorni senza pioggia"},
                ],
                "celle": ids,
                "punto_peggiore": {"lat": peggiore["lat"], "lon": peggiore["lon"]},
                "invaso": {"nome": inv.nome, "distanza_km": round(inv.d / 1000, 1), "riempimento": inv.riempimento}
                if inv else None,
            })
    return {"aggiornato_il": p.inizio, "meteo_simulato": p.simulato, "aree": aree}


def aree_critiche() -> dict:
    return con_cache("aree_critiche", _calcola, durata_s=3600) or _calcola()


def livello_indice(v: float) -> str:
    """Stesse soglie delle aree critiche; sotto, medio e basso."""
    return "molto alto" if v >= SOGLIA_MOLTO_ALTO else "alto" if v >= SOGLIA_ALTO else "medio" if v >= 0.4 else "basso"


def indice_comune(nome: str, lat: float, lon: float) -> float:
    """Massimo indice delle celle del comune; se il comune non ha celle, la cella del punto."""
    p = previsione()
    with engine.connect() as c:
        smax = math.log1p(c.execute(text("SELECT max(storico) FROM cella")).scalar() or 1)
        righe = c.execute(text("SELECT ce.lon, ce.lat, ce.storico, ce.pericolo FROM cella ce JOIN comune co "
                               "ON ST_Intersects(co.geom, ce.geom) WHERE upper(co.nome) = upper(:n)"), {"n": nome}).all()
        if not righe:
            righe = c.execute(text("SELECT lon, lat, storico, pericolo FROM cella "
                                   "ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) LIMIT 1"),
                              {"lon": lon, "lat": lat}).all()
    return max((PESI["storico"] * math.log1p(r.storico) / smax + PESI["pericolo"] * r.pericolo
                + PESI["meteo"] * meteo_peggiore(serie_vicina(p, r.lat, r.lon)) for r in righe), default=0.0)
