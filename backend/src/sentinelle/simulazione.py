"""Simulazione di scenario: tempi di arrivo del fuoco su griglia 200 m con Dijkstra su 8 vicini.
Velocita' = base * combustibile * exp(k * vento * cos) * umidita' * pioggia, con il meteo dell'ora di arrivo.
Modello semplificato e indicativo: niente pendenza."""
import heapq
import math
import time
import tomllib

import numpy as np
import shapely
from shapely import wkb
from sqlalchemy import text

from .config import FILE_PESI
from .db import engine
from .fonti.meteo_orario import Ora, previsione, serie_vicina
from .rischio_oggi import DLAT, DLON

CFG = tomllib.loads(FILE_PESI.read_text())["simulazione"]
PASSO_M = 200
LATO_KM = [40, 70, 100]
M_LAT = 110540.0
VICINI = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
NOTA = ("Scenario indicativo, modello semplificato: automa su griglia 200 m con vento, umidita' e combustibile "
        "stimato (pericolo AIB e storico CFVA). Non considera la pendenza ne' l'intervento dei mezzi.")


def fattori_ora(o: Ora, cfg: dict = CFG) -> list[float]:
    """Moltiplicatore di velocita' per ciascuno degli 8 vicini (riga = nord, colonna = est)."""
    verso = math.radians(o.da_gradi + 180)  # il vento spinge verso da+180
    umid = math.exp(-cfg["k_umidita"] * max(0.0, o.umidita - cfg["umidita_rif"]))
    piog = cfg["pioggia_fattore"] if o.pioggia_mm > 0.5 else 1.0
    out = []
    for dr, dc in VICINI:
        cos = math.cos(math.atan2(dc, dr) - verso)  # angolo da nord in senso orario
        out.append(math.exp(cfg["k_vento"] * o.vento_kmh * cos) * umid * piog)
    return out


def tempi_arrivo(comb: np.ndarray, origine: tuple[int, int], meteo: list[Ora], minuti: float,
                 passo_m: float = PASSO_M, cfg: dict = CFG) -> np.ndarray:
    """Minuti di arrivo per cella (inf = non raggiunta). comb: 0 = non brucia; riga 0 = sud."""
    ny, nx = comb.shape
    fl = comb.ravel().tolist()
    fatt = [fattori_ora(o, cfg) for o in meteo]
    dist = [passo_m * math.hypot(dr, dc) for dr, dc in VICINI]
    offs = [dr * nx + dc for dr, dc in VICINI]
    base = cfg["base_m_min"]
    t = [math.inf] * (ny * nx)
    s = origine[0] * nx + origine[1]
    t[s] = 0.0
    coda = [(0.0, s)]
    while coda:
        tu, u = heapq.heappop(coda)
        if tu > t[u]:
            continue
        r, c = divmod(u, nx)
        f = fatt[min(int(tu // 60), len(fatt) - 1)]
        for k in range(8):
            dr, dc = VICINI[k]
            rr, cc = r + dr, c + dc
            if rr < 0 or cc < 0 or rr >= ny or cc >= nx:
                continue
            v = u + offs[k]
            cv = fl[v]
            if cv <= 0:
                continue
            tv = tu + dist[k] / (base * cv * f[k])
            if tv < t[v] and tv <= minuti:
                t[v] = tv
                heapq.heappush(coda, (tv, v))
    return np.array(t).reshape(ny, nx)


def maschera_poligono(mask: np.ndarray, passo_m: float, x0: float, y0: float):
    """Unione delle celle vere come poligono (coordinate metriche locali), a corse di riga."""
    rett = []
    for r in np.flatnonzero(mask.any(axis=1)):
        riga = np.concatenate(([0], mask[r].view(np.int8), [0]))
        d = np.diff(riga)
        for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            rett.append(shapely.box(x0 + a * passo_m, y0 + r * passo_m, x0 + b * passo_m, y0 + (r + 1) * passo_m))
    return shapely.union_all(rett) if rett else None


# ---------------------------------------------------------------- dati reali e risposta API

def _combustibile(lat0: float, lon0: float, lato_km: float):
    """Griglia di combustibile centrata sul punto + geometrie comuni (metriche) del dominio."""
    mx = M_LAT * math.cos(math.radians(lat0))
    n = int(lato_km * 1000 / PASSO_M) | 1  # dispari: l'origine e' la cella centrale
    meta = n // 2 * PASSO_M
    dlat, dlon = (meta + PASSO_M) / M_LAT, (meta + PASSO_M) / mx
    with engine.connect() as c:
        celle = c.execute(text("SELECT i, j, storico, pericolo FROM cella WHERE geom && ST_MakeEnvelope(:a,:b,:c,:d,4326)"),
                          {"a": lon0 - dlon, "b": lat0 - dlat, "c": lon0 + dlon, "d": lat0 + dlat}).all()
        comuni = c.execute(text("SELECT nome, ST_AsBinary(ST_SimplifyPreserveTopology(geom, 0.0005)) g FROM comune "
                                "WHERE geom && ST_MakeEnvelope(:a,:b,:c,:d,4326)"),
                           {"a": lon0 - dlon, "b": lat0 - dlat, "c": lon0 + dlon, "d": lat0 + dlat}).all()
    smax = math.log1p(max((r.storico for r in celle), default=1) or 1)
    valori = {(r.i, r.j): (CFG["combustibile_min"] + (1 - CFG["combustibile_min"]) * r.pericolo)
              * (1 + CFG["bonus_storico"] * math.log1p(r.storico) / smax) for r in celle}
    a_metri = lambda g: shapely.transform(g, lambda xy: np.column_stack(((xy[:, 0] - lon0) * mx, (xy[:, 1] - lat0) * M_LAT)))
    geo_comuni = [(r.nome, a_metri(wkb.loads(r.g))) for r in comuni]
    terra = shapely.union_all([g for _, g in geo_comuni]) if geo_comuni else None
    xs = (np.arange(n) - n // 2) * PASSO_M  # centri cella
    X, Y = np.meshgrid(xs, xs)
    lat, lon = lat0 + Y / M_LAT, lon0 + X / mx
    I, J = np.floor(lat / DLAT).astype(int), np.floor(lon / DLON).astype(int)
    comb = np.array([valori.get((i, j), 0.0) for i, j in zip(I.ravel(), J.ravel())]).reshape(n, n)
    if terra is not None:
        shapely.prepare(terra)
        comb[~shapely.contains_xy(terra, X, Y)] = 0.0
    return comb, n, mx, geo_comuni


def simula(lat: float, lon: float, ore: int) -> dict:
    t0 = time.time()
    p = previsione()
    serie = serie_vicina(p, lat, lon)
    meteo = serie.ore[:max(ore, 1)] or [Ora(25, 300, 30, 0, 30, 40)]
    for lato in LATO_KM:
        comb, n, mx, geo_comuni = _combustibile(lat, lon, lato)
        c = n // 2
        comb[c, c] = max(comb[c, c], CFG["combustibile_min"])  # il punto di innesco brucia comunque
        arrivo = tempi_arrivo(comb, (c, c), meteo, ore * 60)
        bruciato = np.isfinite(arrivo)
        if not (bruciato[0].any() or bruciato[-1].any() or bruciato[:, 0].any() or bruciato[:, -1].any()):
            break
    x0 = -(n // 2) * PASSO_M - PASSO_M / 2
    a_gradi = lambda g: shapely.transform(g, lambda xy: np.column_stack((lon + xy[:, 0] / mx, lat + xy[:, 1] / M_LAT)))
    fotogrammi, raggiunti, ultimo = [], {}, None
    for h in range(1, ore + 1):
        pol = maschera_poligono(arrivo <= h * 60, PASSO_M, x0, x0)
        o = meteo[min(h - 1, len(meteo) - 1)]
        if pol is not None:
            ultimo = pol
            for nome, g in geo_comuni:
                if nome not in raggiunti and g.intersects(pol):
                    raggiunti[nome] = h
            semplice = pol.simplify(50)
            area = shapely.geometry.mapping(shapely.MultiPolygon(
                [g for g in getattr(a_gradi(semplice), "geoms", [a_gradi(semplice)]) if g.geom_type == "Polygon"]))
        else:
            area = {"type": "MultiPolygon", "coordinates": []}
        fotogrammi.append({"ora": h, "area": area, "ettari": round(float((arrivo <= h * 60).sum()) * PASSO_M ** 2 / 1e4, 1),
                           "fronte_km": round((pol.boundary.length if pol is not None else 0) / 1000, 1),
                           "vento": {"kmh": round(o.vento_kmh), "da_gradi": round(o.da_gradi)}, "umidita": round(o.umidita)})
    return {"origine": {"lat": lat, "lon": lon, "comune": _comune(lat, lon)}, "inizio": p.inizio, "ore": ore, "risoluzione_m": PASSO_M,
            "fotogrammi": fotogrammi,
            "comuni": [{"nome": k, "raggiunto_ora": v} for k, v in sorted(raggiunti.items(), key=lambda kv: kv[1])],
            "acqua": _acqua(ultimo, lat, lon, mx),
            "note": NOTA + (" Meteo non disponibile: vento costante 25 km/h da maestrale." if p.simulato else ""),
            "durata_s": round(time.time() - t0, 2)}


def _comune(lat: float, lon: float) -> str | None:
    with engine.connect() as c:
        return c.execute(text("SELECT nome FROM comune WHERE geom && ST_MakeEnvelope(:x, :y, :x, :y, 4326) "
                              "AND ST_Intersects(geom, ST_SetSRID(ST_MakePoint(:x, :y), 4326)) LIMIT 1"),
                         {"x": lon, "y": lat}).scalar()


def _acqua(pol, lat0: float, lon0: float, mx: float) -> list[dict]:
    with engine.connect() as c:
        righe = c.execute(text(
            "SELECT ST_Y(mc.geom) lat, ST_X(mc.geom) lon FROM missione_completata mc JOIN missione m ON m.id = mc.missione_id "
            "WHERE m.codice = 'punto_acqua' AND mc.geom IS NOT NULL")).all()
        try:
            invasi = c.execute(text("SELECT nome, riempimento, volume_mm3, ST_Y(geom) lat, ST_X(geom) lon FROM invaso WHERE volume_mm3 > 0")).all()
        except Exception:  # tabella assente: si prosegue con i soli punti dei cittadini
            invasi = []
    rif = pol if pol is not None else shapely.Point(0, 0)

    def km(lat, lon):
        return round(rif.distance(shapely.Point((lon - lon0) * mx, (lat - lat0) * M_LAT)) / 1000, 1)

    # Raggi dichiarati: 25 km per i punti segnalati (vasche, piccoli specchi), 40 km per gli invasi,
    # gittata realistica per elicotteri con benna che fanno la spola tra bacino e fronte.
    out = [{"nome": "Punto d'acqua segnalato", "tipo": "punto_acqua", "distanza_km": km(r.lat, r.lon),
            "lat": r.lat, "lon": r.lon} for r in righe]
    out = [a for a in out if a["distanza_km"] <= 25]
    out += [a for a in ({"nome": r.nome, "tipo": "invaso", "distanza_km": km(r.lat, r.lon), "riempimento": r.riempimento,
                         "volume_mm3": r.volume_mm3, "lat": r.lat, "lon": r.lon} for r in invasi) if a["distanza_km"] <= 40]
    return sorted(out, key=lambda a: a["distanza_km"])[:6]
