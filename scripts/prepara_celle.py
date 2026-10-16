"""Precalcola la tabella cella (~2 km) per il rischio di oggi e la simulazione. Idempotente: svuota e ricalcola.
storico = incendi CFVA che toccano la cella pesati per recenza (1 nel 2025, 0,5 nel 2015);
pericolo = classe AIB prevalente per area (Basso..Alto -> 0..1)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))
from sqlalchemy import text  # noqa: E402

from sentinelle.db import engine  # noqa: E402
from sentinelle.gioco import prepara_db  # noqa: E402
from sentinelle.rischio_oggi import DLAT, DLON  # noqa: E402

t0 = time.time()
with engine.begin() as c:
    prepara_db(c)
    c.execute(text("TRUNCATE cella RESTART IDENTITY"))
    c.execute(text("""
        INSERT INTO cella (i, j, lon, lat, geom)
        SELECT i, j, (j + 0.5) * :dlon, (i + 0.5) * :dlat,
               ST_MakeEnvelope(j * :dlon, i * :dlat, (j + 1) * :dlon, (i + 1) * :dlat, 4326)
        FROM generate_series(floor(38.85 / :dlat)::int, floor(41.32 / :dlat)::int) i,
             generate_series(floor(8.12 / :dlon)::int, floor(9.83 / :dlon)::int) j
        WHERE EXISTS (SELECT 1 FROM comune co WHERE ST_Intersects(co.geom,
              ST_MakeEnvelope(j * :dlon, i * :dlat, (j + 1) * :dlon, (i + 1) * :dlat, 4326)))"""),
        {"dlat": DLAT, "dlon": DLON})
    c.execute(text("""
        UPDATE cella SET storico = s.v FROM (
          SELECT ce.id, sum(power(0.5, (2025 - f.anno) / 10.0)) AS v
          FROM cella ce JOIN incendio_storico f ON ST_Intersects(f.geom_semplice, ce.geom)
          GROUP BY ce.id) s WHERE s.id = cella.id"""))
    c.execute(text("""
        UPDATE cella SET pericolo = p.v FROM (
          SELECT DISTINCT ON (ce.id) ce.id, CASE pa.classe WHEN 'Alto' THEN 1.0 WHEN 'Medioalto' THEN 0.75
                 WHEN 'Medio' THEN 0.5 WHEN 'Mediobasso' THEN 0.25 ELSE 0.0 END AS v
          FROM cella ce JOIN pericolo_aib pa ON ST_Intersects(pa.geom, ce.geom)
          ORDER BY ce.id, ST_Area(ST_Intersection(pa.geom, ce.geom)) DESC) p WHERE p.id = cella.id"""))
    r = c.execute(text("SELECT count(*) n, max(storico) ms, avg(pericolo) ap FROM cella")).one()
print(f"celle: {r.n}  storico max {r.ms:.1f}  pericolo medio {r.ap:.2f}  ({time.time() - t0:.0f} s)")
