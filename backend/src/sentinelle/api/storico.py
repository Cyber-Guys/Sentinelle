import json

from fastapi import APIRouter
from sqlalchemy import text

from ..db import engine
from ..fonti import hotspot_sardegna

router = APIRouter()
LIMITE_INCENDI = 2000


@router.get("/comuni")
def comuni():
    with engine.connect() as c:
        righe = c.execute(text("SELECT id, nome FROM comune ORDER BY nome")).all()
    return [{"id": r.id, "nome": r.nome} for r in righe]


@router.get("/utenti")
def utenti():
    with engine.connect() as c:
        righe = c.execute(text(
            "SELECT u.id, u.nome, c.nome AS comune, u.punti FROM utente u "
            "LEFT JOIN comune c ON c.id = u.comune_id ORDER BY u.id")).all()
    return [{"id": r.id, "nome": r.nome, "comune": r.comune, "punti": r.punti} for r in righe]


@router.get("/storico/incendi")
def storico_incendi(bbox: str, anno_da: int = 2005, anno_a: int = 2025):
    minlon, minlat, maxlon, maxlat = (float(v) for v in bbox.split(","))
    with engine.connect() as c:
        righe = c.execute(text("""
            SELECT id, cod_incend, anno, data, comune, ettari_totali, tipologia,
                   ST_AsGeoJSON(geom_semplice) AS g
            FROM incendio_storico
            WHERE geom_semplice && ST_MakeEnvelope(:a, :b, :c, :d, 4326)
              AND anno BETWEEN :anno AND :anno_a
            LIMIT :lim"""), {"lim": LIMITE_INCENDI + 1, "a": minlon, "b": minlat, "c": maxlon, "d": maxlat, "anno": anno_da, "anno_a": anno_a}).all()
    # oltre il limite si risponde comunque, ma lo si dichiara: niente troncamento silenzioso
    return {"type": "FeatureCollection", "troncato": len(righe) > LIMITE_INCENDI, "features": [
        {"type": "Feature", "geometry": json.loads(r.g), "properties": {
            "id": r.id, "cod_incend": r.cod_incend, "anno": r.anno, "data": str(r.data) if r.data else None,
            "comune": r.comune, "ettari_totali": r.ettari_totali, "tipologia": r.tipologia}}
        for r in righe[:LIMITE_INCENDI]]}


@router.get("/storico/statistiche")
def storico_statistiche(comune: str | None = None, anno_da: int = 2005, anno_a: int = 2025):
    """Incendi ed ettari per anno, calcolati in SQL (senza geometrie). Senza comune: tutta la Sardegna."""
    with engine.connect() as c:
        righe = c.execute(text("""
            SELECT anno, count(*) AS incendi, coalesce(sum(ettari_totali), 0) AS ettari
            FROM incendio_storico
            WHERE anno BETWEEN :da AND :a AND (CAST(:c AS text) IS NULL OR comune = upper(CAST(:c AS text)))
            GROUP BY anno ORDER BY anno"""), {"c": comune, "da": anno_da, "a": anno_a}).all()
    per_anno = [{"anno": r.anno, "incendi": r.incendi, "ettari": round(float(r.ettari), 2)} for r in righe]
    return {"comune": comune.upper() if comune else None, "per_anno": per_anno,
            "totale_incendi": sum(r["incendi"] for r in per_anno),
            "totale_ettari": round(sum(r["ettari"] for r in per_anno), 2)}


@router.get("/hotspot")
def hotspot():
    hs = hotspot_sardegna() or []
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [h.lon, h.lat]},
         "properties": {"rilevato_il": h.rilevato_il.isoformat(), "confidenza": h.confidenza}} for h in hs]}
