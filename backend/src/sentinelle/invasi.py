"""Invasi sardi (CeDoc Regione Sardegna) come fonti d'acqua per i mezzi aerei: tabella `invaso` da dati/invasi.json."""
import json

from sqlalchemy import text

from .config import RADICE

FILE = RADICE / "dati" / "invasi.json"


def carica(conn) -> None:
    """Ricrea il contenuto di `invaso` dal JSON versionato (idempotente, vale anche per chi ripristina il dump)."""
    conn.execute(text("CREATE TABLE IF NOT EXISTS invaso (id serial PRIMARY KEY, nome text NOT NULL, "
                      "capacita_mm3 float, volume_mm3 float, riempimento int, data_dato text, fonte text, "
                      "geom geometry(Point,4326))"))
    if not FILE.exists():
        return
    d = json.loads(FILE.read_text())
    conn.execute(text("DELETE FROM invaso"))
    conn.execute(text("INSERT INTO invaso (nome, capacita_mm3, volume_mm3, riempimento, data_dato, fonte, geom) "
                      "VALUES (:nome, :capacita_mm3, :volume_mm3, :riempimento, :data, :fonte, "
                      "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))"),
                 [{**i, "data": d["data_dato"], "fonte": d["fonte"]} for i in d["invasi"]])


def geojson(conn) -> dict:
    righe = conn.execute(text("SELECT nome, capacita_mm3, volume_mm3, riempimento, data_dato, fonte, "
                              "ST_X(geom) lon, ST_Y(geom) lat FROM invaso ORDER BY nome")).mappings().all()
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
         "properties": {k: r[k] for k in ("nome", "capacita_mm3", "volume_mm3", "riempimento", "data_dato", "fonte")}}
        for r in righe]}
