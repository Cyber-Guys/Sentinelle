"""Dashboard COP: aree di competenza, bollettino CFD, vedette, fuochi autorizzati, incendi (piano 2026-10-17-dashboard-cop).

SIMULATO e dichiarato nella dashboard: bollettino CFD (deterministico per giorno), vedette, fuochi autorizzati e
gli incendi dimostrativi (stato in memoria: si azzera al riavvio). Reali: comuni, basi, invasi, storico CFVA.
Confini delle aree approssimati: ogni comune va alla sede del servizio territoriale CFVA piu' vicina.
"""
import hashlib
import json
import math
import random
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text

from .config import RADICE
from .db import engine

METRICO = 32632  # UTM 32N: buffer e aree in metri
DIR_BOLLETTINI = RADICE / "dati" / "bollettini"  # scripts/genera_bollettino.py
ORE_AREA_SPENTA = 72  # dopo la chiusura l'area bruciata resta sulla mappa come "spenta"

SEDI = [  # id, nome, lon, lat (servizi territoriali CFVA)
    ("sassari", "Sassari", 8.5557, 40.7259),
    ("tempio", "Tempio Pausania", 9.1046, 40.9006),
    ("nuoro", "Nuoro", 9.3297, 40.3209),
    ("oristano", "Oristano", 8.5920, 39.9037),
    ("lanusei", "Lanusei", 9.5420, 39.8790),
    ("iglesias", "Iglesias", 8.5370, 39.3110),
    ("cagliari", "Cagliari", 9.1217, 39.2238),
]
_SEDI_SQL = "(VALUES " + ", ".join(f"('{i}', {lon}, {lat})" for i, _, lon, lat in SEDI) + ") AS sedi(id, lon, lat)"
_ASSEGNA = (f"SELECT c.id AS comune_id, c.nome, c.geom, (SELECT sedi.id FROM {_SEDI_SQL} ORDER BY "
            "ST_PointOnSurface(c.geom) <-> ST_SetSRID(ST_MakePoint(sedi.lon, sedi.lat), 4326) LIMIT 1) AS area FROM comune c")


def _rng(*chiavi) -> random.Random:
    return random.Random(int(hashlib.sha1("|".join(map(str, chiavi)).encode()).hexdigest()[:12], 16))


@lru_cache(maxsize=1)
def aree() -> dict:
    f = DIR_BOLLETTINI / "aree-cop.json"  # scritto dal generatore insieme ai bollettini
    return json.loads(f.read_text()) if f.exists() else calcola_aree()


def calcola_aree() -> dict:
    with engine.connect() as c:
        righe = c.execute(text(
            f"WITH a AS ({_ASSEGNA}) SELECT area, count(*) AS comuni, "
            f"ST_AsGeoJSON(ST_SimplifyPreserveTopology(ST_Union(geom), 0.002), 5) AS g, "
            f"ST_XMin(ST_Extent(geom)) o, ST_YMin(ST_Extent(geom)) s, ST_XMax(ST_Extent(geom)) e, ST_YMax(ST_Extent(geom)) n "
            f"FROM a GROUP BY area")).all()
    per_id = {r.area: r for r in righe}
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": json.loads(per_id[i].g), "properties": {
            "id": i, "nome": nome, "sede": [lon, lat], "comuni": per_id[i].comuni,
            "bbox": [round(per_id[i].o, 4), round(per_id[i].s, 4), round(per_id[i].e, 4), round(per_id[i].n, 4)]}}
        for i, nome, lon, lat in SEDI if i in per_id]}


def _area_di(lon: float, lat: float) -> str:
    """Sede piu' vicina: stessa regola usata per i confini."""
    k = math.cos(math.radians(lat))
    return min(SEDI, key=lambda s: ((s[2] - lon) * k) ** 2 + (s[3] - lat) ** 2)[0]


# ---------------------------------------------------------------- bollettino CFD (simulato)

def _pericolo(lon: float, lat: float, giorno: date) -> float:
    """Campo liscio 0-1 da 4 rilievi gaussiani posizionati dal giorno: comuni vicini hanno livelli simili."""
    r = _rng("cfd", giorno.isoformat())
    v = 0.18
    for k in range(4):
        cx, cy = r.uniform(8.4, 9.7), r.uniform(39.1, 41.0)
        amp, sig = (0.75 if k == 0 else r.uniform(0.35, 0.6)), r.uniform(0.18, 0.35)
        v += amp * math.exp(-(((lon - cx) * 0.77) ** 2 + (lat - cy) ** 2) / (2 * sig ** 2))
    return min(v, 1.0)


LIVELLI = [("verde", "Pericolo basso"), ("arancione", "Pericolo medio"), ("rosso", "Pericolo alto")]
SOGLIE = {"arancione": 0.42, "rosso": 0.64}


def file_bollettino(giorno: date) -> Path:
    return DIR_BOLLETTINI / f"bollettino-{giorno.isoformat()}.json"


@lru_cache(maxsize=8)
def bollettino(giorno: date) -> dict:
    """Il server NON calcola il bollettino (buffer su tutta l'isola: ~10 s e molta RAM, ha bloccato portatili con
    poca memoria). Legge i file prodotti da scripts/genera_bollettino.py; se manca il giorno usa il file del giorno
    piu' vicino, dichiarandolo in `ripiego_da`. Senza file: tutto verde e `mancante: true`."""
    if file_bollettino(giorno).exists():
        return json.loads(file_bollettino(giorno).read_text())
    disponibili = sorted(DIR_BOLLETTINI.glob("bollettino-*.json"))
    if not disponibili:
        verde = {"verde": 1.0, "arancione": 0.0, "rosso": 0.0, "massimo": "verde"}
        return {"simulato": True, "mancante": True, "fonte": "Nessun bollettino generato: scripts/genera_bollettino.py",
                "valido_per": giorno.isoformat(), "emesso_il": _emissione(giorno), "per_area": {s[0]: verde for s in SEDI},
                "zone": {"type": "FeatureCollection", "features": []}}
    vicino = min(disponibili, key=lambda f: abs((date.fromisoformat(f.stem.removeprefix("bollettino-")) - giorno).days))
    b = json.loads(vicino.read_text())
    return {**b, "ripiego_da": b["valido_per"], "valido_per": giorno.isoformat(), "emesso_il": _emissione(giorno)}


def _emissione(giorno: date) -> str:
    """Il CFD emette il bollettino il giorno prima, alle 14."""
    return datetime.combine(giorno - timedelta(days=1), datetime.min.time()).replace(hour=14).isoformat()


def calcola_bollettino(giorno: date) -> dict:
    """Calcolo vero e proprio, solo da scripts/genera_bollettino.py."""
    with engine.begin() as c:
        comuni = c.execute(text("SELECT id, ST_X(ST_PointOnSurface(geom)) lon, ST_Y(ST_PointOnSurface(geom)) lat FROM comune")).all()
        livello = {r.id: ("rosso" if (v := _pericolo(r.lon, r.lat, giorno)) >= SOGLIE["rosso"]
                          else "arancione" if v >= SOGLIE["arancione"] else "verde") for r in comuni}
        c.execute(text("CREATE TEMP TABLE liv (id int, livello text) ON COMMIT DROP"))
        c.execute(text("INSERT INTO liv VALUES (:id, :l)"), [{"id": k, "l": v} for k, v in livello.items()])
        # comuni semplificati a 250 m in metri: i buffer sulle geometrie piene costano minuti
        c.execute(text(f"CREATE TEMP TABLE cs ON COMMIT DROP AS SELECT liv.livello, "
                       f"ST_SimplifyPreserveTopology(ST_Transform(co.geom, {METRICO}), 250) g FROM comune co JOIN liv USING (id)"))
        # Zone annidate (arancione contiene rosso): unione dei comuni, chiusura + apertura morfologica in metri
        # e smussatura di Chaikin -> contorni curvi, ritagliati sulla costa. Verde = tutta l'isola.
        c.execute(text(f"""
            CREATE TEMP TABLE zone ON COMMIT DROP AS
            WITH isola AS (SELECT ST_Buffer(ST_Buffer(ST_Union(g), 600), -600) g FROM cs),  -- chiude le fessure tra comuni semplificati
            z AS (
              SELECT 'arancione' AS livello, ST_Union(g) g FROM cs WHERE livello IN ('arancione', 'rosso')
              UNION ALL
              SELECT 'rosso', ST_Union(g) FROM cs WHERE livello = 'rosso'),
            m AS (
              SELECT livello, ST_ChaikinSmoothing(ST_SimplifyPreserveTopology(
                ST_Buffer(ST_Buffer(ST_Buffer(ST_Buffer(g, 4000, 'quad_segs=8'), -4000, 'quad_segs=8'), -2500, 'quad_segs=8'), 2500, 'quad_segs=8'),
                400), 3) g FROM z WHERE g IS NOT NULL)
            SELECT 'verde' AS livello, g FROM isola
            UNION ALL
            SELECT m.livello, ST_Intersection(m.g, isola.g) FROM m, isola WHERE NOT ST_IsEmpty(m.g)"""))
        righe = c.execute(text("SELECT livello, ST_AsGeoJSON(ST_Transform(ST_SimplifyPreserveTopology(g, 150), 4326), 5) gj "
                                "FROM zone WHERE NOT ST_IsEmpty(g)")).all()
        c.execute(text("CREATE TEMP TABLE ar (id text, g geometry) ON COMMIT DROP"))
        c.execute(text(f"INSERT INTO ar VALUES (:id, ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326), {METRICO}))"),
                  [{"id": f["properties"]["id"], "g": json.dumps(f["geometry"])} for f in aree()["features"]])
        quote = c.execute(text("SELECT ar.id, z.livello, ST_Area(ST_Intersection(ar.g, z.g)) / ST_Area(ar.g) q "
                               "FROM ar JOIN zone z ON z.livello <> 'verde' AND ar.g && z.g")).all()
        per_area = {}
        for aid in (f["properties"]["id"] for f in aree()["features"]):
            q = {r.livello: r.q for r in quote if r.id == aid}
            rosso = round(q.get("rosso", 0), 3)
            arancione = round(max(q.get("arancione", 0) - rosso, 0), 3)
            per_area[aid] = {"rosso": rosso, "arancione": arancione, "verde": round(max(1 - rosso - arancione, 0), 3),
                             "massimo": "rosso" if rosso > 0.01 else "arancione" if arancione > 0.01 else "verde"}
    nomi = dict(LIVELLI)
    return {"simulato": True, "fonte": "Centro Funzionale Decentrato, Protezione Civile Sardegna (bollettino simulato)",
            "valido_per": giorno.isoformat(), "emesso_il": _emissione(giorno), "per_area": per_area,
            "zone": {"type": "FeatureCollection", "features": [
                {"type": "Feature", "geometry": json.loads(r.gj), "properties": {"livello": r.livello, "etichetta": nomi[r.livello]}}
                for r in righe]}}


# ---------------------------------------------------------------- vedette e fuochi autorizzati (simulati)

@lru_cache(maxsize=1)
def vedette() -> dict:
    with engine.connect() as c:
        righe = c.execute(text(f"WITH a AS ({_ASSEGNA}) SELECT area, nome, ST_X(ST_PointOnSurface(geom)) lon, "
                               "ST_Y(ST_PointOnSurface(geom)) lat FROM a ORDER BY md5(nome)")).all()
    per_area: dict[str, list] = {}
    for r in righe:
        if len(per_area.setdefault(r.area, [])) < 4:
            per_area[r.area].append(r)
    out = []
    for aid, lista in per_area.items():
        for k, r in enumerate(lista):
            g = _rng("vedetta", r.nome)
            out.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(r.lon + g.uniform(-.02, .02), 5), round(r.lat + g.uniform(-.02, .02), 5)]},
                        "properties": {"id": f"v-{aid}-{k}", "nome": f"Vedetta {r.nome.title()}", "area": aid,
                                       "raggio_km": g.choice([12, 15, 15, 18]), "stato": "Presidiata" if g.random() > 0.2 else "Non presidiata"}})
    return {"type": "FeatureCollection", "simulato": True, "features": out}


TIPI_FUOCO = ["Abbruciamento residui vegetali", "Pulizia fondo agricolo", "Bruciatura ramaglie di potatura"]


def fuochi(oggi: date) -> dict:
    r = _rng("fuochi", oggi.isoformat())
    with engine.connect() as c:
        comuni = c.execute(text("SELECT nome, ST_X(ST_PointOnSurface(geom)) lon, ST_Y(ST_PointOnSurface(geom)) lat FROM comune ORDER BY id")).all()
    ora = datetime.now().hour
    out = []
    for k, co in enumerate(r.sample(comuni, 30)):
        dalle = r.choice([6, 7, 8, 15, 16])
        stato = "In corso" if dalle <= ora < dalle + 3 else "Concluso" if ora >= dalle + 3 else "Programmato"
        out.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(co.lon + r.uniform(-.015, .015), 5), round(co.lat + r.uniform(-.015, .015), 5)]},
                    "properties": {"id": f"f{k}", "comune": co.nome.title(), "area": _area_di(co.lon, co.lat), "tipo": r.choice(TIPI_FUOCO),
                                   "data": oggi.isoformat(), "dalle": f"{dalle:02d}:00", "alle": f"{dalle + 3:02d}:00",
                                   "ettari": round(r.uniform(0.2, 2.5), 1), "stato": stato}})
    return {"type": "FeatureCollection", "simulato": True, "features": out}


# ---------------------------------------------------------------- incendi (dimostrativi + da segnalazioni)

def _sagoma(lon: float, lat: float, raggio_m: float, seme: str, vento: float) -> list:
    """Perimetro morbido e allungato nella direzione del vento (armoniche casuali, niente cerchi perfetti)."""
    g = _rng("sagoma", seme)
    armoniche = [(k, g.uniform(0.04, 0.16) / k ** 0.6, g.uniform(0, 2 * math.pi)) for k in range(2, 6)]
    k_lon = 111320 * math.cos(math.radians(lat))
    punti = []
    for i in range(72):
        t = 2 * math.pi * i / 72
        r = raggio_m * (1 + sum(a * math.sin(k * t + f) for k, a, f in armoniche))
        x, y = r * 1.7 * math.cos(t), r * math.sin(t)  # ellisse lungo il vento
        rx, ry = x * math.cos(vento) - y * math.sin(vento), x * math.sin(vento) + y * math.cos(vento)
        punti.append([round(lon + (rx + raggio_m * 0.5 * math.cos(vento)) / k_lon, 5), round(lat + (ry + raggio_m * 0.5 * math.sin(vento)) / 111320, 5)])
    return [punti + [punti[0]]]


def _ettari(anello: list, lat: float) -> float:
    k = 111320 * math.cos(math.radians(lat))
    a = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anello, anello[1:]))
    return round(abs(a) / 2 * k * 111320 / 10000, 1)


_ADESSO = datetime.now(timezone.utc)
DEMO = [  # id, nome, comune, lon, lat, raggio_m, vento (rad), ore dall'innesco, ore dalla chiusura (None = attivo)
    ("d1", "Incendio Sinnai - Bruncu Mogumu", "Sinnai", 9.235, 39.335, 650, 0.6, 3.5, None),
    ("d2", "Incendio Montiferru", "Santu Lussurgiu", 8.640, 40.120, 900, 0.3, 6.0, None),
    ("d3", "Incendio Orune - Su Gologone", "Orune", 9.390, 40.425, 420, -0.4, 1.2, None),
    ("d4", "Incendio Ittiri", "Ittiri", 8.585, 40.585, 380, 1.0, 20.0, 9.0),
    ("d5", "Incendio Villacidro", "Villacidro", 8.700, 39.460, 520, 0.2, 40.0, 30.0),
    ("d6", "Incendio Tortolì - Bellavista", "Tortolì", 9.645, 39.930, 300, 0.8, 2.0, None),
]
_stato_demo: dict[str, datetime | None] = {d[0]: (_ADESSO - timedelta(hours=d[8]) if d[8] is not None else None) for d in DEMO}


def incendi() -> dict:
    adesso = datetime.now(timezone.utc)
    out = []
    for i, nome, comune, lon, lat, raggio, vento, ore, _ in DEMO:
        spento = _stato_demo[i]
        if spento and adesso - spento > timedelta(hours=ORE_AREA_SPENTA):
            continue
        anello = _sagoma(lon, lat, raggio, i, vento)
        out.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": anello}, "properties": {
            "id": i, "nome": nome, "comune": comune, "area": _area_di(lon, lat), "stato": "spento" if spento else "attivo",
            "inizio": (_ADESSO - timedelta(hours=ore)).isoformat(), "spento_il": spento.isoformat() if spento else None,
            "ettari": _ettari(anello[0], lat), "fronte_m": round(raggio * 2.6, -1), "centro": [lon, lat], "origine": "simulato"}})
    with engine.connect() as c:
        righe = c.execute(text(
            "SELECT s.id, ST_X(s.geom) lon, ST_Y(s.geom) lat, s.creata_il, s.stato_ufficiale, s.aggiornata_il, "
            "(SELECT nome FROM comune co WHERE ST_Intersects(co.geom, s.geom) LIMIT 1) comune FROM segnalazione s "
            "WHERE s.tipo IN ('fuoco', 'fumo') AND s.stato = 'confermata' AND (s.stato_ufficiale <> 'spento' "
            "OR s.aggiornata_il > now() - make_interval(hours => :h))"), {"h": ORE_AREA_SPENTA}).all()
    # segnalazioni certificate entro 2,5 km = un solo incendio (capogruppo = la piu' vecchia)
    gruppi: list[list] = []
    for r in sorted(righe, key=lambda r: r.creata_il):
        g = next((g for g in gruppi if _km(g[0], r) <= 2.5), None)
        (g.append(r) if g else gruppi.append([r]))
    for g in gruppi:
        r = g[0]
        lon, lat = sum(x.lon for x in g) / len(g), sum(x.lat for x in g) / len(g)
        anello = _sagoma(lon, lat, 260 + 60 * (len(g) - 1), f"s{r.id}", 0.5)
        spento = all(x.stato_ufficiale == "spento" for x in g)
        comune = (r.comune or "").title()
        out.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": anello}, "properties": {
            "id": f"s{r.id}", "nome": f"Incendio {comune or 'segnalato'}", "comune": comune, "area": _area_di(lon, lat),
            "stato": "spento" if spento else "attivo", "inizio": r.creata_il.isoformat(),
            "spento_il": max(x.aggiornata_il for x in g).isoformat() if spento else None, "ettari": _ettari(anello[0], lat),
            "fronte_m": 680, "centro": [lon, lat], "origine": "segnalazione", "segnalazione_id": r.id,
            "segnalazioni": [x.id for x in g]}})
    return {"type": "FeatureCollection", "ore_area_spenta": ORE_AREA_SPENTA, "features": out}


def _km(a, b) -> float:
    return math.hypot((a.lon - b.lon) * 111.32 * math.cos(math.radians(a.lat)), (a.lat - b.lat) * 110.57)


def concludi(id: str) -> dict | None:
    if id in _stato_demo:
        _stato_demo[id] = _stato_demo[id] or datetime.now(timezone.utc)
    elif id.startswith("s") and id[1:].isdigit():
        from .api.segnalazioni import StatoUfficiale, imposta_stato
        f = next((f for f in incendi()["features"] if f["properties"]["id"] == id), None)
        for sid in (f["properties"]["segnalazioni"] if f else [int(id[1:])]):  # tutto il gruppo
            imposta_stato(sid, StatoUfficiale(stato_ufficiale="spento"))
    return next((f for f in incendi()["features"] if f["properties"]["id"] == id), None)


# ---------------------------------------------------------------- statistiche per area (storico CFVA reale)

@lru_cache(maxsize=16)
def statistiche(area: str) -> dict:
    g = next((json.dumps(f["geometry"]) for f in aree()["features"] if f["properties"]["id"] == area), None)
    if g is None:
        return {}
    with engine.connect() as c:
        c.execute(text("SET LOCAL statement_timeout = '20s'"))
        righe = c.execute(text("""
            WITH a AS (SELECT ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326) g)
            SELECT i.anno, extract(month FROM i.data)::int AS mese, count(*) n,
                   coalesce(sum(i.ettari_totali) FILTER (WHERE i.ettari_totali < 20000), 0) ha  -- scarta i record palesemente errati
            FROM incendio_storico i, a WHERE i.anno >= 2015 AND i.geom_semplice && a.g
              AND ST_Intersects(a.g, ST_PointOnSurface(i.geom_semplice))
            GROUP BY i.anno, mese"""), {"g": g}).all()
    media, ultimo = [0.0] * 12, [0] * 12
    anni: dict[int, dict] = {}
    for r in righe:
        a = anni.setdefault(r.anno, {"anno": r.anno, "incendi": 0, "ettari": 0.0})
        a["incendi"] += r.n
        a["ettari"] += float(r.ha)
        if r.mese:
            if r.anno == 2025:
                ultimo[r.mese - 1] += r.n
            else:
                media[r.mese - 1] += r.n / 10
    return {"area": area, "mesi_media": [round(v, 1) for v in media], "mesi_2025": ultimo,
            "anni": [{**v, "ettari": round(v["ettari"])} for _, v in sorted(anni.items())]}


def scalda() -> None:
    """Aree e vedette pronte all'avvio (pochi secondi). Il bollettino no: si legge da file."""
    aree()
    vedette()


def avvisati(segnalazione_id: int) -> int:
    """Utenti dell'app con una localita' monitorata entro 5 km o residenti nel comune della segnalazione."""
    with engine.connect() as c:
        return c.execute(text(
            "WITH s AS (SELECT geom FROM segnalazione WHERE id = :i) SELECT count(DISTINCT u.id) FROM utente u, s "
            "WHERE EXISTS (SELECT 1 FROM localita l WHERE l.utente_id = u.id AND ST_DWithin(l.geom::geography, s.geom::geography, 5000)) "
            "OR u.comune_id = (SELECT co.id FROM comune co WHERE ST_Intersects(co.geom, s.geom) LIMIT 1)"),
            {"i": segnalazione_id}).scalar() or 0
