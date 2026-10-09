import json

from fastapi import APIRouter
from sqlalchemy import text

from ..db import engine
from ..fonti import hotspot_sardegna

router = APIRouter()


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
            LIMIT 2000"""), {"a": minlon, "b": minlat, "c": maxlon, "d": maxlat, "anno": anno_da, "anno_a": anno_a}).all()
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": json.loads(r.g), "properties": {
            "id": r.id, "cod_incend": r.cod_incend, "anno": r.anno, "data": str(r.data) if r.data else None,
            "comune": r.comune, "ettari_totali": r.ettari_totali, "tipologia": r.tipologia}}
        for r in righe]}


@router.get("/hotspot")
def hotspot():
    hs = hotspot_sardegna() or []
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [h.lon, h.lat]},
         "properties": {"rilevato_il": h.rilevato_il.isoformat(), "confidenza": h.confidenza}} for h in hs]}
