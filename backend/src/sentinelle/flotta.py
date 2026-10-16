"""Flotta SIMULATA (dimostrativa): mezzi di terra e aerei con stato funzione deterministica del tempo.

Stesso t -> stessa flotta per tutti i client. Traiettorie rettilinee, nessun instradamento stradale.
Terra: pattuglia ad anello attorno alla base, oppure i 3 mezzi piu' vicini (entro 60 km) vanno sull'obiettivo
a 50 km/h e restano "Sul posto". Aerei: base -> invaso piu' vicino all'obiettivo (carico) -> obiettivo (lancio) -> invaso...
Obiettivi: incendi attivi (FIRMS) e segnalazioni confermate / allertati / mezzi sul posto non spente.
"""
import math
import zlib
from datetime import datetime

from sqlalchemy import text

from . import basi, incendi_attivi

V_TERRA, V_ELI, V_CAN = 50, 200, 300  # km/h
SOSTA_CARICO, SOSTA_LANCIO = 90, 45  # s
N_TERRA = 25
ELI = ["I-HBAA", "I-HBAB", "I-HBAC", "I-HBAD", "I-HBAE", "I-HBAF"]


def km(a, b):  # (lat, lon)
    dl, do = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dl / 2) ** 2 + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(do / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def rotta(a, b):
    y = math.sin(math.radians(b[1] - a[1])) * math.cos(math.radians(b[0]))
    x = math.cos(math.radians(a[0])) * math.sin(math.radians(b[0])) - math.sin(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.cos(math.radians(b[1] - a[1]))
    return round((math.degrees(math.atan2(y, x)) + 360) % 360)


def lungo(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def h(s: str) -> int:
    return zlib.crc32(s.encode())


def composizione(lb: list[dict]) -> list[dict]:
    """Mezzi fissi (deterministici) assegnati alle basi."""
    terra_b = [b for b in lb if b["ente"] in ("VVF", "CFVA")]
    out = []
    for i in range(min(N_TERRA, len(terra_b))):
        b = terra_b[i * len(terra_b) // N_TERRA]
        vvf = b["ente"] == "VVF"
        tipo = ("Autobotte pompa" if i % 2 else "APS (partenza)") if vvf else "Fuoristrada AIB"
        out.append({"id": f"t{i}", "sigla": f"VF {23400 + i * 7}" if vvf else f"CFVA {101 + i}", "tipo": tipo,
                    "categoria": "terra", "ente": "Vigili del Fuoco" if vvf else "Corpo Forestale", "base": b})
    eli = [b for b in lb if b["ente"] == "AIB" and "elicotteri" in b["tipo"]]
    for i, s in enumerate(ELI[:len(eli)]):
        out.append({"id": f"e{i}", "sigla": s, "tipo": "Elicottero AIB", "categoria": "aereo", "ente": "Regione Sardegna (AIB)",
                    "base": eli[(i * len(eli)) // len(ELI)], "v": V_ELI})
    can = [b for b in lb if b["tipo"] == "base Canadair"]
    for i in range(2 if can else 0):
        out.append({"id": f"c{i}", "sigla": f"CAN-{28 + i}", "tipo": "Canadair CL-415", "categoria": "aereo",
                    "ente": "Stato (COAU)", "base": can[0], "v": V_CAN})
    return out


def mezzi_per_base(conn) -> dict:
    mb: dict = {}
    for m in composizione(basi.elenco(conn)):
        mb.setdefault(m["base"]["id"], []).append(f"{m['sigla']} · {m['tipo']}")
    return mb


def obiettivi(conn) -> list[dict]:
    out = []
    try:
        for f in incendi_attivi.incendi_attivi()["features"]:
            p = f["properties"]
            out.append({"nome": f"Incendio attivo{' · ' + p['comune'] if p.get('comune') else ''}",
                        "pos": (p["centro"][1], p["centro"][0]), "t0": datetime.fromisoformat(p["prima"]).timestamp(), "peso": p["rilevazioni"]})
    except Exception:  # noqa: BLE001 FIRMS non raggiungibile: restano le segnalazioni
        pass
    righe = conn.execute(text(
        "SELECT id, ST_Y(geom) lat, ST_X(geom) lon, extract(epoch from coalesce(valutata_il, aggiornata_il, creata_il)) t0 "
        "FROM segnalazione WHERE stato_ufficiale <> 'spento' AND tipo = 'fuoco' "
        "AND (stato = 'confermata' OR stato_ufficiale IN ('allertati', 'mezzi_sul_posto')) "
        "AND creata_il > now() - interval '48 hours'")).all()
    out += [{"nome": f"Segnalazione #{r.id}", "pos": (r.lat, r.lon), "t0": float(r.t0), "peso": 50} for r in righe]
    return sorted(out, key=lambda o: -o["peso"])


_TERRA: dict = {}  # cache: percorsi gia' riportati a terra


def a_terra(conn, chiave, punti, rif=None):
    """I punti in mare vengono spostati sul punto di costa piu' vicino (unione dei comuni), ~300 m all'interno."""
    if chiave not in _TERRA:
        if "isola" not in _TERRA:
            _TERRA["isola"] = conn.execute(text("SELECT ST_AsEWKB(ST_Buffer(ST_Union(geom), -0.003)) FROM comune")).scalar()
        wkt = "MULTIPOINT(" + ",".join(f"({lo} {la})" for la, lo in punti) + ")"
        righe = conn.execute(text(
            # solo la terra su cui sta il primo punto (base): niente salti tra isole attraverso il mare
            "WITH i AS (SELECT d.geom g FROM ST_Dump(ST_GeomFromEWKB(:isola)) d "
            "ORDER BY d.geom <-> ST_SetSRID(ST_MakePoint(:lo0, :la0), 4326) LIMIT 1), "
            "p AS (SELECT d.geom g, d.path[1] k FROM ST_Dump(ST_GeomFromText(:w, 4326)) d), "
            "q AS (SELECT k, CASE WHEN ST_Intersects(p.g, i.g) THEN p.g ELSE ST_ClosestPoint(i.g, p.g) END g FROM p, i) "
            "SELECT ST_Y(g) la, ST_X(g) lo FROM q ORDER BY k"), {"isola": _TERRA["isola"], "w": wkt, "la0": (rif or punti[0])[0], "lo0": (rif or punti[0])[1]}).all()
        _TERRA[chiave] = [(r.la, r.lo) for r in righe]
    return _TERRA[chiave]


def raggio_a_terra(conn, chiave, raggi, anello):
    """Primo raggio il cui anello di pattuglia sta tutto a terra (nessun tratto sul mare)."""
    if ("r", chiave) not in _TERRA:
        a_terra(conn, "_", [(40.0, 9.0)])  # assicura l'isola in cache
        _TERRA[("r", chiave)] = next((r for r in raggi if conn.execute(text(
            "SELECT ST_Within(ST_GeomFromText(:w, 4326), ST_GeomFromEWKB(:isola))"),
            {"w": "LINESTRING(" + ",".join(f"{lo} {la}" for la, lo in anello(r)) + ")", "isola": _TERRA["isola"]}).scalar()), None)
    return _TERRA[("r", chiave)]


def su_percorso(pp, f):
    """Punto alla frazione f di una spezzata (distanze in km)."""
    tratti = [km(a, b) for a, b in zip(pp, pp[1:])]
    s = f * sum(tratti)
    for (a, b), d in zip(zip(pp, pp[1:]), tratti):
        if s <= d:
            return lungo(a, b, s / d if d else 1)
        s -= d
    return pp[-1]


def pos_terra(m, t, ob, conn):
    b = a_terra(conn, ("b", m["id"]), [(m["base"]["lat"], m["base"]["lon"])])[0]
    if ob:
        pp = a_terra(conn, ("v", m["id"], ob["pos"]), [lungo(b, ob["pos"], i / 200) for i in range(201)], b)
        d = sum(km(a, c) for a, c in zip(pp, pp[1:]))
        fatto = max(0.0, (t - ob["t0"]) * V_TERRA / 3600)
        if fatto >= d:
            hh = h(m["id"])  # sul posto: sparsi di ~300 m, non impilati
            ang = (hh % 360) * math.pi / 180
            return (ob["pos"][0] + 0.003 * math.cos(ang), ob["pos"][1] + 0.004 * math.sin(ang)), "Sul posto", ob["nome"], rotta(b, ob["pos"]), 0
        p, nx = su_percorso(pp, fatto / d), su_percorso(pp, min(1.0, (fatto + 0.2) / d))
        return p, "In movimento", ob["nome"], rotta(p, nx), V_TERRA
    hh = h(m["id"])
    if hh % 3 == 0:
        return b, "In base", m["base"]["nome"], 0, 0
    ang0, verso = (hh % 360) * math.pi / 180, (1 if hh % 2 else -1)
    anello = lambda r: [(b[0] + r / 111 * math.cos(ang0 + verso * k * math.pi / 36),
                         b[1] + r / (111 * math.cos(math.radians(b[0]))) * math.sin(ang0 + verso * k * math.pi / 36)) for k in range(73)]
    r = raggio_a_terra(conn, m["id"], [5 + hh % 11, 8, 5, 3, 2, 1], anello)
    if r is None:  # costa troppo frastagliata o isola piccola: resta in base
        return b, "In base", m["base"]["nome"], 0, 0
    anello = anello(r)
    f = ((t * V_TERRA / 3600) / (2 * math.pi * r)) % 1
    p, nx = su_percorso(anello, f), su_percorso(anello, (f + 0.005) % 1)
    return p, "Pattuglia", f"Pattuglia attorno a {m['base']['comune']}", rotta(p, nx), V_TERRA


def pos_aereo(m, t, ob, invasi):
    b = (m["base"]["lat"], m["base"]["lon"])
    v = m["v"]
    if not ob:
        hh = h(m["id"])
        if hh % 2 == 0:
            return b, "In base", m["base"]["nome"], 0, 0
        # ricognizione breve: anello di 12 km, 20 minuti in volo ogni ora
        s = t % 3600
        if s > 1200:
            return b, "In base", m["base"]["nome"], 0, 0
        ang = s * v / 3600 / 12
        p = (b[0] + 12 / 111 * math.sin(ang), b[1] + 12 / 85 * (1 - math.cos(ang)))
        return p, "Ricognizione", f"Ricognizione da {m['base']['comune']}", round((90 - math.degrees(ang)) % 360), v
    inv = min(invasi, key=lambda i: km(i["pos"], ob["pos"])) if invasi else {"nome": "Mare", "pos": ob["pos"]}
    legs = [(b, inv["pos"], "In volo", inv["nome"]), (inv["pos"], inv["pos"], "Carico acqua", inv["nome"]),
            (inv["pos"], ob["pos"], "In volo", ob["nome"]), (ob["pos"], ob["pos"], "Lancio", ob["nome"])]
    dur = lambda a, c, s: SOSTA_CARICO if s == "Carico acqua" else SOSTA_LANCIO if s == "Lancio" else km(a, c) / v * 3600
    s = max(0.0, t - ob["t0"])
    primo = dur(*legs[0][:2], legs[0][2])
    if s < primo:
        return lungo(b, inv["pos"], s / primo if primo else 1), "In volo", inv["nome"], rotta(b, inv["pos"]), v
    s -= primo
    ciclo = legs[1:] + [(ob["pos"], inv["pos"], "In volo", inv["nome"])]
    tot = sum(dur(a, c, st) for a, c, st, _ in ciclo)
    s = s % tot if tot else 0
    for a, c, st, nome in ciclo:
        d = dur(a, c, st)
        if s <= d:
            return lungo(a, c, s / d if d else 1), st, nome, rotta(a, c) if a != c else 0, v if st == "In volo" else 0
        s -= d
    return ob["pos"], "Lancio", ob["nome"], 0, 0


def assegna(mezzi, obs):
    """Terra: i 3 mezzi liberi piu' vicini entro 60 km per obiettivo. Aerei: 2 elicotteri entro 150 km, Canadair sul piu' grande."""
    ass: dict = {}
    for o in obs:
        cand = sorted((km((m["base"]["lat"], m["base"]["lon"]), o["pos"]), m["id"]) for m in mezzi if m["categoria"] == "terra" and m["id"] not in ass)
        for d, i in [c for c in cand if c[0] <= 60][:3]:
            ass[i] = o
        cand = sorted((km((m["base"]["lat"], m["base"]["lon"]), o["pos"]), m["id"]) for m in mezzi if m["tipo"] == "Elicottero AIB" and m["id"] not in ass)
        for d, i in [c for c in cand if c[0] <= 150][:2]:
            ass[i] = o
    if obs:
        for m in mezzi:
            if m["tipo"].startswith("Canadair"):
                ass[m["id"]] = obs[0]
    return ass


def stato(conn, t: float) -> dict:
    lb = basi.elenco(conn)
    mezzi = composizione(lb)
    obs = obiettivi(conn)
    invasi = [{"nome": r.nome, "pos": (r.lat, r.lon)} for r in conn.execute(text("SELECT nome, ST_Y(geom) lat, ST_X(geom) lon FROM invaso WHERE coalesce(volume_mm3, 1) > 0"))]
    ass = assegna(mezzi, obs)
    out = []
    for m in mezzi:
        ob = ass.get(m["id"])
        if ob and m["id"] == "c1":  # il secondo Canadair parte 7 minuti dopo: non si sovrappone al primo
            ob = {**ob, "t0": ob["t0"] + 420}
        f = pos_aereo if m["categoria"] == "aereo" else pos_terra
        (p, st, dest, rt, v), (p2, *_) = f(m, t, ob, invasi) if m["categoria"] == "aereo" else f(m, t, ob, conn), \
            (f(m, t + 10, ob, invasi) if m["categoria"] == "aereo" else f(m, t + 10, ob, conn))
        out.append({"id": m["id"], "sigla": m["sigla"], "tipo": m["tipo"], "categoria": m["categoria"], "ente": m["ente"],
                    "base": m["base"]["nome"], "stato": st, "destinazione": dest, "lat": round(p[0], 5), "lon": round(p[1], 5),
                    "lat_poi": round(p2[0], 5), "lon_poi": round(p2[1], 5), "rotta": rt, "velocita_kmh": v})
    return {"t": t, "passo_s": 10, "simulazione": True, "obiettivi": len(obs), "mezzi": out}
