"""Basi operative antincendio (VVF, CFVA, basi elicotteri AIB): tabella `base` da dati/basi.json (scripts/aggiorna_basi.py)."""
import json

from sqlalchemy import text

from .config import RADICE

FILE = RADICE / "dati" / "basi.json"
CAMPI = ("id", "nome", "ente", "tipo", "comune", "indirizzo", "coord_incerta", "fonte")


def carica(conn) -> None:
    conn.execute(text("CREATE TABLE IF NOT EXISTS base (id text PRIMARY KEY, nome text NOT NULL, ente text NOT NULL, "
                      "tipo text, comune text, indirizzo text, coord_incerta bool, fonte text, geom geometry(Point,4326))"))
    if not FILE.exists():
        return
    conn.execute(text("DELETE FROM base"))
    conn.execute(text("INSERT INTO base (id, nome, ente, tipo, comune, indirizzo, coord_incerta, fonte, geom) VALUES "
                      "(:id, :nome, :ente, :tipo, :comune, :indirizzo, :coord_incerta, :fonte, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))"),
                 json.loads(FILE.read_text())["basi"])


def elenco(conn) -> list[dict]:
    return [dict(r) for r in conn.execute(text(
        f"SELECT {', '.join(CAMPI)}, ST_Y(geom) lat, ST_X(geom) lon FROM base ORDER BY ente, id")).mappings()]


def geojson(conn) -> dict:
    from .flotta import mezzi_per_base
    mb = mezzi_per_base(conn)
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [b["lon"], b["lat"]]},
         "properties": {**{k: b[k] for k in CAMPI}, "mezzi": mb.get(b["id"], [])}} for b in elenco(conn)]}
