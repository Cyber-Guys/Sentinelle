"""API della webapp cittadino: utenti, localita' monitorate, avvisi con priorita', storico, ricerca luoghi."""
import math
import re
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from shapely.geometry import box, mapping
from shapely.ops import unary_union
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..aree_critiche import _accenta, livello_indice
from ..config import impostazioni
from ..db import engine
from ..fonti.cache import con_cache
from ..fonti.http import client
from ..rischio_oggi import DLAT, DLON, griglia
from . import gioco as _gioco
from .segnalazioni import _filtro_attive

router = APIRouter()

UA = {"User-Agent": "SentinelleHackathon/1.0 (webapp cittadino, demo)"}
SOGLIA_ZONA = 0.4          # da "medio" in su una cella e' una zona a rischio
URGENTE_ENTRO_KM = 2.0     # fuoco entro 2 km = avviso urgente
BBOX_SARDEGNA = "7.9,41.4,10.0,38.7"   # viewbox Nominatim: ovest,nord,est,sud
ETICHETTE = {"fuoco": "Fuoco", "fumo": "Fumo", "area_a_rischio": "Terreno a rischio"}
ORDINE = {"urgente": 0, "importante": 1, "informazione": 2}
AMMESSI = {"urgenti": {"urgente"}, "urgenti_importanti": {"urgente", "importante"},
           "tutti": {"urgente", "importante", "informazione"}}

LOCALITA = ("SELECT l.id, l.utente_id, l.nome, l.tipo, l.indirizzo, ST_Y(l.geom) AS lat, ST_X(l.geom) AS lon, "
            "l.avvisi_attivi, l.avvisi_tipi, l.raggio_km, l.urgenza FROM localita l")


# --- utenti ------------------------------------------------------------------------------------------

class UtenteIn(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    telefono: str | None = Field(None, max_length=24)


class UtenteMod(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=60)
    telefono: str | None = Field(None, max_length=24)


def _telefono(t: str | None) -> str | None:
    t = re.sub(r"[^0-9+ ]", "", t or "").strip()
    return t or None


@router.post("/utenti", status_code=201)
def crea_utente(u: UtenteIn):
    with Session(engine) as s:
        id = s.execute(text("INSERT INTO utente (nome, telefono) VALUES (:n, :t) RETURNING id"),
                       {"n": u.nome.strip(), "t": _telefono(u.telefono)}).scalar()
        s.commit()
    return _gioco.utente(id)


@router.patch("/utenti/{id}")
def modifica_utente(id: int, u: UtenteMod):
    campi = u.model_dump(exclude_unset=True)
    if "nome" in campi and campi["nome"]:
        campi["nome"] = campi["nome"].strip()
    if "telefono" in campi:
        campi["telefono"] = _telefono(campi["telefono"])
    if campi:
        with Session(engine) as s:
            ok = s.execute(text("UPDATE utente SET " + ", ".join(f"{k} = :{k}" for k in campi) + " WHERE id = :id"),
                           {**campi, "id": id}).rowcount
            if not ok:
                raise HTTPException(404, "utente non trovato")
            s.commit()
    return _gioco.utente(id)


# --- rischio e zone attorno a un punto ---------------------------------------------------------------

_cache_celle: dict = {"t": 0.0, "celle": [], "simulato": False}


def celle() -> tuple[list, bool]:
    """Griglia del rischio di oggi (la stessa del cruscotto), ricalcolata al piu' ogni 5 minuti."""
    if time.time() - _cache_celle["t"] > 300:
        g = griglia()
        _cache_celle.update(t=time.time(), celle=[tuple(c) for c in g["celle"]], simulato=bool(g["meteo_simulato"]))
    return _cache_celle["celle"], _cache_celle["simulato"]


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def zone(lat: float, lon: float, raggio_km: int) -> tuple[int, dict, float]:
    """Celle a rischio (da 'medio') entro il raggio: (numero di zone contigue, GeoJSON con le celle unite per
    livello, valore massimo)."""
    tutte, _ = celle()
    vicine = [c for c in tutte if c[2] >= SOGLIA_ZONA and km(lat, lon, c[1], c[0]) <= raggio_km + 1.5]
    idx = {(round(c[1] / DLAT - 0.5), round(c[0] / DLON - 0.5)) for c in vicine}
    visti, n = set(), 0
    for k in idx:
        if k in visti:
            continue
        n += 1
        pila = [k]
        visti.add(k)
        while pila:
            i, j = pila.pop()
            for q in ((i + a, j + b) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                if q in idx and q not in visti:
                    visti.add(q)
                    pila.append(q)
    per_livello: dict[str, list] = {}
    for c in vicine:
        i, j = round(c[1] / DLAT - 0.5), round(c[0] / DLON - 0.5)  # bordi esatti sulla griglia: le celle vicine si fondono
        per_livello.setdefault(livello_indice(c[2]), []).append(box(j * DLON, i * DLAT, (j + 1) * DLON, (i + 1) * DLAT))
    feats = [{"type": "Feature", "properties": {"livello": liv}, "geometry": mapping(unary_union(per_livello[liv]))}
             for liv in ("medio", "alto", "molto alto") if liv in per_livello]  # dal meno al piu' grave: l'ultimo sta sopra
    return n, {"type": "FeatureCollection", "features": feats}, max((c[2] for c in vicine), default=0.0)


# --- avvisi ------------------------------------------------------------------------------------------

def _fa(minuti: int) -> str:
    return "ora" if minuti < 1 else f"{minuti} min fa" if minuti < 90 else f"{round(minuti / 60)} h fa"


def _decimale(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def avvisi_utente(s: Session, utente_id: int) -> list[dict]:
    """Avvisi attivi per le localita' con avvisi accesi, ordinati per priorita' e distanza."""
    out = []
    for l in s.execute(text(LOCALITA + " WHERE l.utente_id = :u AND l.avvisi_attivi ORDER BY l.id"), {"u": utente_id}).all():
        ammessi = AMMESSI[l.urgenza]
        punto = "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography"
        righe = s.execute(text(
            f"SELECT s.id, s.tipo, ST_Y(s.geom) AS lat, ST_X(s.geom) AS lon, s.creata_il, "
            f"ST_Distance(s.geom::geography, {punto}) / 1000 AS d, (extract(epoch FROM now() - s.creata_il) / 60)::int AS eta "
            f"FROM segnalazione s WHERE {_filtro_attive()} AND s.stato_ufficiale <> 'spento' "
            f"AND ST_DWithin(s.geom::geography, {punto}, :r) ORDER BY d"),
            {"lat": l.lat, "lon": l.lon, "r": l.raggio_km * 1000}).all()
        for r in righe:
            if r.tipo not in l.avvisi_tipi:
                continue
            pr = "urgente" if r.tipo == "fuoco" and r.d <= URGENTE_ENTRO_KM else \
                "importante" if r.tipo in ("fuoco", "fumo") else "informazione"
            if pr in ammessi:
                out.append({"id": f"{l.id}:{r.id}", "priorita": pr, "tipo": r.tipo, "segnalazione_id": r.id,
                            "titolo": f"{ETICHETTE[r.tipo]} vicino a {l.nome}" if r.d < 0.15 else
                                      f"{ETICHETTE[r.tipo]} a {_decimale(r.d)} km da {l.nome}",
                            "testo": f"Segnalato {_fa(r.eta)}", "localita_id": l.id, "localita_nome": l.nome,
                            "distanza_km": round(r.d, 1), "lat": r.lat, "lon": r.lon, "da_lat": l.lat, "da_lon": l.lon,
                            "creato_il": r.creata_il.isoformat()})
        if "informazione" in ammessi:
            n, geo, massimo = zone(l.lat, l.lon, l.raggio_km)
            if n and livello_indice(massimo) in ("alto", "molto alto"):
                out.append({"id": f"{l.id}:rischio", "priorita": "informazione", "tipo": "rischio", "segnalazione_id": None,
                            "titolo": f"Rischio {livello_indice(massimo)} oggi vicino a {l.nome}",
                            "testo": f"{n} {'zona' if n == 1 else 'zone'} a rischio entro {l.raggio_km} km",
                            "localita_id": l.id, "localita_nome": l.nome, "distanza_km": None, "lat": l.lat, "lon": l.lon,
                            "da_lat": l.lat, "da_lon": l.lon, "creato_il": None})
    return sorted(out, key=lambda a: (ORDINE[a["priorita"]], a["distanza_km"] if a["distanza_km"] is not None else 99))


@router.get("/utenti/{id}/avvisi")
def avvisi(id: int):
    with Session(engine) as s:
        _gioco._utente(s, id)
        return avvisi_utente(s, id)


# --- localita' ---------------------------------------------------------------------------------------

class LocalitaIn(BaseModel):
    nome: str = Field(min_length=1, max_length=40)
    tipo: Literal["casa", "terreno", "vigna", "altro"] = "altro"
    indirizzo: str | None = Field(None, max_length=160)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    avvisi_attivi: bool = True
    avvisi_tipi: list[Literal["fuoco", "fumo", "area_a_rischio"]] = ["fuoco", "fumo"]
    raggio_km: Literal[2, 5, 10] = 5
    urgenza: Literal["urgenti", "urgenti_importanti", "tutti"] = "urgenti_importanti"


class LocalitaMod(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=40)
    indirizzo: str | None = Field(None, max_length=160)
    avvisi_attivi: bool | None = None
    avvisi_tipi: list[Literal["fuoco", "fumo", "area_a_rischio"]] | None = None
    raggio_km: Literal[2, 5, 10] | None = None
    urgenza: Literal["urgenti", "urgenti_importanti", "tutti"] | None = None


def _json_localita(s: Session, l, tutti_avvisi: list[dict]) -> dict:
    n, geo, massimo = zone(l.lat, l.lon, l.raggio_km)
    mie = [a for a in tutti_avvisi if a["localita_id"] == l.id]
    nseg = s.execute(text(
        f"SELECT count(*) FROM segnalazione s WHERE {_filtro_attive()} AND s.stato_ufficiale <> 'spento' AND "
        "ST_DWithin(s.geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :r)"),
        {"lat": l.lat, "lon": l.lon, "r": l.raggio_km * 1000}).scalar()
    return {"id": l.id, "utente_id": l.utente_id, "nome": l.nome, "tipo": l.tipo, "indirizzo": l.indirizzo,
            "lat": l.lat, "lon": l.lon, "avvisi_attivi": l.avvisi_attivi, "avvisi_tipi": list(l.avvisi_tipi),
            "raggio_km": l.raggio_km, "urgenza": l.urgenza,
            "stato": {"livello": livello_indice(massimo), "n_zone": n, "zone": geo, "n_segnalazioni": nseg,
                      "n_avvisi": len(mie), "priorita_max": mie[0]["priorita"] if mie else None,
                      "meteo_simulato": celle()[1]}}


def _carica(s: Session, id: int):
    l = s.execute(text(LOCALITA + " WHERE l.id = :i"), {"i": id}).one_or_none()
    if l is None:
        raise HTTPException(404, "localita' non trovata")
    return l


@router.get("/utenti/{id}/localita")
def elenco_localita(id: int):
    with Session(engine) as s:
        _gioco._utente(s, id)
        av = avvisi_utente(s, id)
        return [_json_localita(s, l, av) for l in s.execute(text(LOCALITA + " WHERE l.utente_id = :u ORDER BY l.id"), {"u": id}).all()]


@router.post("/utenti/{id}/localita", status_code=201)
def crea_localita(id: int, l: LocalitaIn):
    with Session(engine) as s:
        _gioco._utente(s, id)
        nuova = s.execute(text(
            "INSERT INTO localita (utente_id, nome, tipo, indirizzo, geom, avvisi_attivi, avvisi_tipi, raggio_km, urgenza) "
            "VALUES (:u, :n, :t, :ind, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :aa, :at, :r, :ur) RETURNING id"),
            {"u": id, "n": l.nome.strip(), "t": l.tipo, "ind": l.indirizzo, "lat": l.lat, "lon": l.lon,
             "aa": l.avvisi_attivi, "at": l.avvisi_tipi, "r": l.raggio_km, "ur": l.urgenza}).scalar()
        # la prima casa decide il comune dell'utente (classifica dei comuni)
        if l.tipo == "casa":
            s.execute(text("UPDATE utente SET comune_id = (SELECT c.id FROM comune c WHERE ST_Intersects(c.geom, "
                           "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) LIMIT 1) WHERE id = :u AND comune_id IS NULL"),
                      {"lon": l.lon, "lat": l.lat, "u": id})
        s.commit()
        return _json_localita(s, _carica(s, nuova), avvisi_utente(s, id))


@router.get("/localita/{id}")
def dettaglio_localita(id: int):
    with Session(engine) as s:
        l = _carica(s, id)
        return _json_localita(s, l, avvisi_utente(s, l.utente_id))


@router.patch("/localita/{id}")
def modifica_localita(id: int, m: LocalitaMod):
    campi = m.model_dump(exclude_unset=True, exclude_none=True)
    with Session(engine) as s:
        _carica(s, id)
        if campi:
            s.execute(text("UPDATE localita SET " + ", ".join(f"{k} = :{k}" for k in campi) + " WHERE id = :id"),
                      {**campi, "id": id})
            s.commit()
        l = _carica(s, id)
        return _json_localita(s, l, avvisi_utente(s, l.utente_id))


@router.delete("/localita/{id}", status_code=204)
def elimina_localita(id: int):
    with Session(engine) as s:
        _carica(s, id)
        s.execute(text("DELETE FROM localita WHERE id = :i"), {"i": id})
        s.commit()
    return Response(status_code=204)


# --- storico dell'utente -----------------------------------------------------------------------------

def _titolo(nome: str | None) -> str | None:
    return _accenta(nome.title()) if nome else None


@router.get("/utenti/{id}/storico")
def storico(id: int):
    with Session(engine) as s:
        _gioco._utente(s, id)
        casa = s.execute(text("SELECT nome FROM localita WHERE utente_id = :u AND tipo = 'casa' ORDER BY id LIMIT 1"),
                         {"u": id}).scalar()
        righe = s.execute(text(
            "SELECT s.id, s.tipo, ST_Y(s.geom) AS lat, ST_X(s.geom) AS lon, s.foto, s.video, s.nota, s.direzione, s.stato, "
            "s.stato_ufficiale, s.creata_il, (SELECT c.nome FROM comune c WHERE ST_Intersects(c.geom, s.geom) LIMIT 1) AS comune, "
            "ST_Distance(s.geom::geography, h.geom::geography) / 1000 AS km_casa "
            "FROM segnalazione s LEFT JOIN LATERAL (SELECT geom FROM localita WHERE utente_id = :u AND tipo = 'casa' "
            "ORDER BY id LIMIT 1) h ON true WHERE s.utente_id = :u ORDER BY s.creata_il DESC"), {"u": id}).all()
    return {"casa_nome": casa, "segnalazioni": [
        {"id": r.id, "tipo": r.tipo, "lat": r.lat, "lon": r.lon, "creata_il": r.creata_il.isoformat(),
         "foto_url": f"/foto/{r.foto}" if r.foto else None, "video_url": f"/foto/{r.video}" if r.video else None,
         "nota": r.nota, "direzione": r.direzione, "stato": r.stato, "stato_ufficiale": r.stato_ufficiale,
         "comune": _titolo(r.comune), "km_casa": round(r.km_casa, 1) if r.km_casa is not None else None} for r in righe]}


# --- luoghi: comune di un punto e ricerca per indirizzo ----------------------------------------------

def _nominatim(percorso: str, **par):
    """None senza rete (o in modalita' offline): la webapp ripiega sui comuni del database."""
    if impostazioni.modalita_offline:
        return None
    try:
        r = client.get("https://nominatim.openstreetmap.org/" + percorso, headers=UA, timeout=4,
                       params={"format": "jsonv2", "accept-language": "it", **par})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@router.get("/luogo")
def luogo(lat: float, lon: float):
    with engine.connect() as c:
        comune = c.execute(text("SELECT nome FROM comune WHERE ST_Intersects(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) "
                                "LIMIT 1"), {"lon": lon, "lat": lat}).scalar()
    r = con_cache(f"luogo:{lat:.4f}:{lon:.4f}", lambda: _nominatim("reverse", lat=lat, lon=lon, zoom=17) or {}, 86400)
    a = (r or {}).get("address", {})
    via = a.get("road") or a.get("pedestrian") or a.get("hamlet")
    indirizzo = (f"{via} {a['house_number']}" if via and a.get("house_number") else via)
    return {"comune": _titolo(comune), "indirizzo": indirizzo}


@router.get("/cerca")
def cerca(q: str):
    q = q.strip()
    if len(q) < 2:
        return []
    r = con_cache(f"cerca:{q.lower()}", lambda: _nominatim("search", q=q, countrycodes="it", viewbox=BBOX_SARDEGNA,
                                                          bounded=1, limit=5, addressdetails=0), 3600)
    if r:
        return [{"nome": ", ".join(x["display_name"].split(", ")[:3]), "lat": float(x["lat"]), "lon": float(x["lon"]),
                 "approssimato": False} for x in r]
    # senza rete: centro del comune che compare nel testo
    pezzi = [p for p in re.split(r"[,\s]+", q) if len(p) >= 3]
    with engine.connect() as c:
        for p in reversed(pezzi):
            righe = c.execute(text("SELECT nome, ST_Y(ST_PointOnSurface(geom)) AS lat, ST_X(ST_PointOnSurface(geom)) AS lon "
                                   "FROM comune WHERE nome ILIKE :p ORDER BY nome LIMIT 5"), {"p": p + "%"}).all()
            if righe:
                return [{"nome": f"{_titolo(x.nome)} (centro del comune)", "lat": x.lat, "lon": x.lon, "approssimato": True}
                        for x in righe]
    return []
