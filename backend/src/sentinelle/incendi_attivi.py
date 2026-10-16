"""Incendi attivi: hotspot FIRMS vicini (catena entro ~750 m) raggruppati in un unico incendio.
Area = unione dei pixel VIIRS (quadrati 375 m centrati sugli hotspot)."""
import math

import numpy as np
import shapely

from .fonti import hotspot_sardegna
from .simulazione import M_LAT, _comune

PIXEL_M = 375.0
SOGLIA_M = 750.0
_memo: dict = {}


def raggruppa(punti: list[tuple[float, float]], soglia_m: float = SOGLIA_M) -> list[list[int]]:
    """Indici raggruppati per catena di distanze <= soglia (union-find). punti = (lat, lon)."""
    padre = list(range(len(punti)))

    def radice(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    for i, (la, lo) in enumerate(punti):
        mx = M_LAT * math.cos(math.radians(la))
        for j in range(i + 1, len(punti)):
            lb, lob = punti[j]
            if math.hypot((lob - lo) * mx, (lb - la) * M_LAT) <= soglia_m:
                padre[radice(i)] = radice(j)
    gruppi: dict[int, list[int]] = {}
    for i in range(len(punti)):
        gruppi.setdefault(radice(i), []).append(i)
    return list(gruppi.values())


def _area(punti: list[tuple[float, float]]):
    """Poligono in gradi (EPSG:4326) e ettari dell'unione dei pixel."""
    lat0 = sum(p[0] for p in punti) / len(punti)
    lon0 = sum(p[1] for p in punti) / len(punti)
    mx = M_LAT * math.cos(math.radians(lat0))
    h = PIXEL_M / 2
    pol = shapely.union_all([shapely.box((lo - lon0) * mx - h, (la - lat0) * M_LAT - h,
                                         (lo - lon0) * mx + h, (la - lat0) * M_LAT + h) for la, lo in punti])
    gradi = shapely.transform(pol, lambda xy: np.column_stack((lon0 + xy[:, 0] / mx, lat0 + xy[:, 1] / M_LAT)))
    return gradi, round(pol.area / 1e4, 1), lat0, lon0


def calcola(hs) -> dict:
    gruppi = raggruppa([(h.lat, h.lon) for h in hs])
    feats = []
    for g in sorted(gruppi, key=lambda g: -len(g)):
        sel = [hs[i] for i in g]
        geom, ettari, lat0, lon0 = _area([(h.lat, h.lon) for h in sel])
        frp = [h.frp for h in sel if h.frp is not None]
        conf = [h.confidenza for h in sel]
        ordine = {"h": 3, "high": 3, "n": 2, "nominal": 2, "l": 1, "low": 1}
        tempi = sorted(h.rilevato_il for h in sel)
        feats.append({"type": "Feature", "geometry": shapely.geometry.mapping(geom), "properties": {
            "id": f"ia-{tempi[0]:%Y%m%d%H%M}-{lat0:.3f}-{lon0:.3f}",
            "rilevazioni": len(sel), "ettari": ettari,
            "prima": tempi[0].isoformat(), "ultima": tempi[-1].isoformat(),
            "frp_totale": round(sum(frp), 1) if frp else None, "frp_max": round(max(frp), 1) if frp else None,
            "confidenza": max(conf, key=lambda c: ordine.get(str(c).lower(), 0)),
            "satelliti": sorted({h.satellite for h in sel if h.satellite}),
            "comune": _comune(lat0, lon0), "centro": [round(lon0, 5), round(lat0, 5)],
            "punti": [[h.lon, h.lat] for h in sel]}})
    return {"type": "FeatureCollection", "features": feats}


def incendi_attivi() -> dict:
    hs = hotspot_sardegna() or []
    if not hs:
        return {"type": "FeatureCollection", "features": []}
    # la lista FIRMS in cache resta lo stesso oggetto finche' non si aggiorna: memo allineata
    if _memo.get("hs") is not hs:
        _memo.update(hs=hs, out=calcola(hs))
    return _memo["out"]
