"""Missioni mirate dal rischio: ogni giorno 2-3 punti da controllare nelle celle piu' a rischio vicino al comune."""
import math
from datetime import datetime, time, timedelta

from sqlalchemy import text

from .aree_critiche import aree_critiche
from .gioco import FUSO, oggi
from .rischio_oggi import PESI, meteo_peggiore
from .fonti.meteo_orario import previsione, serie_vicina

RAGGIO_KM = 15
DISTANZA_MIN_KM = 4
QUANTE = 3
RAGGIO_COMPLETAMENTO_M = 1000
LIVELLI = [(0.7, "molto alto", 40), (0.6, "alto", 30), (0.0, "medio", 20)]
DIREZIONI = ["nord", "nord-est", "est", "sud-est", "sud", "sud-ovest", "ovest", "nord-ovest"]


def km(lon1, lat1, lon2, lat2) -> float:
    dx = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, (lat2 - lat1) * 110.57)


def livello(v: float) -> tuple[str, int]:
    return next((nome, punti) for soglia, nome, punti in LIVELLI if v >= soglia)


def scegli(celle: list[dict], n: int = QUANTE, distanza_min: float = DISTANZA_MIN_KM) -> list[dict]:
    """Le n celle a rischio piu' alto (prima quelle dentro un'area critica di oggi), scartando quelle a meno di distanza_min km da una gia' scelta."""
    scelte = []
    for c in sorted(celle, key=lambda c: -(c["valore"] + (0.2 if c.get("critica") else 0))):
        if all(km(c["lon"], c["lat"], s["lon"], s["lat"]) >= distanza_min for s in scelte):
            scelte.append(c)
            if len(scelte) == n:
                break
    return scelte


def _dove(c: dict, comune: str, clon: float, clat: float) -> str:
    if c["dist_km"] < 2:
        return f"a {comune}"
    ang = math.degrees(math.atan2((c["lon"] - clon) * math.cos(math.radians(clat)), c["lat"] - clat)) % 360
    return f"a {DIREZIONI[round(ang / 45) % 8]} di {comune}"


def _genera(conn, utente_id: int) -> None:
    u = conn.execute(text(
        "SELECT initcap(lower(c.nome)) AS comune, ST_X(ST_Centroid(c.geom)) AS lon, ST_Y(ST_Centroid(c.geom)) AS lat "
        "FROM utente u JOIN comune c ON c.id = u.comune_id WHERE u.id = :u"), {"u": utente_id}).one_or_none()
    if u is None:
        return
    righe = conn.execute(text(
        "SELECT id, lon, lat, storico, pericolo FROM cella WHERE ST_DWithin(geom::geography, "
        "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :r)"), {"lon": u.lon, "lat": u.lat, "r": RAGGIO_KM * 1000}).all()
    if not righe:
        return
    smax = math.log1p(conn.execute(text("SELECT max(storico) FROM cella")).scalar() or 1)
    p = previsione()
    celle = []
    for r in righe:
        s = serie_vicina(p, r.lat, r.lon)
        v = (PESI["storico"] * math.log1p(r.storico) / smax + PESI["pericolo"] * r.pericolo
             + PESI["meteo"] * meteo_peggiore(s))
        ore = s.ore[:24]
        celle.append({"id": r.id, "lon": r.lon, "lat": r.lat, "valore": round(v, 3), "pericolo": r.pericolo,
                      "raffiche": max((o.raffiche_kmh for o in ore), default=0),
                      "umidita": min((o.umidita for o in ore), default=50),
                      "dist_km": km(u.lon, u.lat, r.lon, r.lat)})
    critiche = {i for a in aree_critiche()["aree"] for i in a["celle"]}
    for c in celle:
        c["critica"] = c["id"] in critiche
    domani = oggi() + timedelta(days=1)
    scade = datetime.combine(domani, time(20), FUSO)
    for c in scegli(celle):
        nome, punti = livello(c["valore"])
        incendi = conn.execute(text(
            "SELECT count(*) FROM incendio_storico f JOIN cella ce ON ST_Intersects(f.geom_semplice, ce.geom) "
            "WHERE ce.id = :c AND f.anno >= 2005"), {"c": c["id"]}).scalar()
        dati = [f"raffiche fino a {c['raffiche']:.0f} km/h", f"umidità minima {c['umidita']:.0f}%"]
        if incendi:
            dati.append(f"{incendi} {'incendio' if incendi == 1 else 'incendi'} passati di qui dal 2005")
        if c["pericolo"] >= 0.75:
            dati.append("vegetazione a pericolo AIB alto")
        titolo = f"Rischio {nome} oggi {_dove(c, u.comune, u.lon, u.lat)}"
        testo = ", ".join(dati)
        motivo = f"{testo[0].upper()}{testo[1:]}: controlla sterpaglie e rifiuti in quest'area."
        conn.execute(text(
            "INSERT INTO missione_mirata (utente_id, cella_id, geom, titolo, motivo, punti, valore_rischio, scade_il) "
            "VALUES (:u, :c, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :t, :m, :p, :v, :s)"),
            {"u": utente_id, "c": c["id"], "lon": c["lon"], "lat": c["lat"], "t": titolo, "m": motivo,
             "p": punti, "v": c["valore"], "s": scade})


GIORNO = "(creata_il AT TIME ZONE 'Europe/Rome')::date"


def di_oggi(conn, utente_id: int) -> list[dict]:
    """Missioni mirate di oggi dell'utente, generate alla prima richiesta del giorno."""
    conn.execute(text("SELECT pg_advisory_xact_lock(4242, :u)"), {"u": utente_id})
    q = text(f"SELECT mm.id, mm.titolo, mm.motivo, mm.punti, mm.valore_rischio, mm.scade_il, mm.completata_il, "
             "ST_X(mm.geom) AS lon, ST_Y(mm.geom) AS lat, ST_Distance(mm.geom::geography, ST_Centroid(c.geom)::geography) AS dist "
             "FROM missione_mirata mm JOIN utente u ON u.id = mm.utente_id JOIN comune c ON c.id = u.comune_id "
             f"WHERE mm.utente_id = :u AND {GIORNO.replace('creata_il', 'mm.creata_il')} = :g ORDER BY mm.valore_rischio DESC")
    righe = conn.execute(q, {"u": utente_id, "g": oggi()}).all()
    if not righe:
        _genera(conn, utente_id)
        righe = conn.execute(q, {"u": utente_id, "g": oggi()}).all()
    return [{"id": r.id, "titolo": r.titolo, "motivo": r.motivo, "punti": r.punti, "valore_rischio": r.valore_rischio,
             "livello_rischio": livello(r.valore_rischio)[0], "lon": r.lon, "lat": r.lat,
             "distanza_km": round(r.dist / 1000, 1), "scade_il": r.scade_il.isoformat(),
             "completata": r.completata_il is not None} for r in righe]
