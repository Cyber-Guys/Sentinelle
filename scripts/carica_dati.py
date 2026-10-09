"""Carica i GeoJSON di dati/ in PostGIS. Idempotente: svuota e ricarica."""
import json, os
from pathlib import Path
import psycopg
from campi_incendi import comune as nome_comune, data_incendio, ettari_bosco, ettari_totali, primo

DATI = Path(__file__).resolve().parent.parent / "dati"
URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://sentinelle:sentinelle@localhost:5432/sentinelle").replace("+psycopg", "")
GEOM = "ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_Force2D(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))), 3))"


def geom(f):
    return json.dumps(f["geometry"])


with psycopg.connect(URL) as con, con.cursor() as cur:
    # DB esistenti: colonna e indice per la geometria semplificata (i nuovi ambienti li hanno da schema.sql)
    cur.execute("ALTER TABLE incendio_storico ADD COLUMN IF NOT EXISTS geom_semplice geometry(MultiPolygon,4326)")
    cur.execute("CREATE INDEX IF NOT EXISTS incendio_storico_geom_semplice_idx ON incendio_storico USING gist (geom_semplice)")
    # tabelle del gioco (sezione "-- gioco:" di schema.sql, IF NOT EXISTS) prima del TRUNCATE ... CASCADE
    cur.execute("--" + (Path(__file__).resolve().parent.parent / "infra" / "schema.sql").read_text().split("-- gioco:", 1)[1])
    cur.execute("TRUNCATE comune, incendio_storico, pericolo_aib, utente, segnalazione RESTART IDENTITY CASCADE")

    for f in json.loads((DATI / "comuni.geojson").read_text())["features"]:
        cur.execute(f"INSERT INTO comune (nome, geom) VALUES (%s, {GEOM})", (f["properties"]["nome"].upper(), geom(f)))

    for f in json.loads((DATI / "pericolo_aib.geojson").read_text())["features"]:
        cur.execute(f"INSERT INTO pericolo_aib (classe, geom) VALUES (%s, {GEOM})", (f["properties"]["valore"], geom(f)))

    for anno in range(2005, 2026):
        path = DATI / f"perimetri_{anno}.geojson"
        if not path.exists():
            print("manca", anno)
            continue
        for f in json.loads(path.read_text())["features"]:
            p = f["properties"]
            cur.execute(
                f"INSERT INTO incendio_storico (cod_incend, anno, data, comune, ettari_totali, ettari_bosco, tipologia, geom) "
                f"VALUES (%s,%s,%s,%s,%s,%s,%s,{GEOM})",
                (primo(p, ["cod_incend", "id_ince", "numincen", "numeroincendio", "numeroince"]), anno,
                 data_incendio(p), nome_comune(p), ettari_totali(p), ettari_bosco(p),
                 primo(p, ["tipologia", "tipologie"]), geom(f)))

    cur.execute("""UPDATE incendio_storico SET geom_semplice =
                   ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom, 0.0005)), 3))""")
    cur.execute("ANALYZE incendio_storico")

    # 5 utenti di demo nei 2 comuni con piu' incendi 2020-2025
    cur.execute("""SELECT c.id, c.nome FROM incendio_storico i JOIN comune c ON c.nome = i.comune
                   WHERE i.anno >= 2020 GROUP BY c.id, c.nome ORDER BY count(*) DESC LIMIT 2""")
    top = cur.fetchall()
    nomi = ["Giulia", "Marco", "Sara", "Luca", "Elena"]
    for i, n in enumerate(nomi):
        cur.execute("INSERT INTO utente (nome, comune_id) VALUES (%s, %s)", (n, top[i % 2][0]))
    print("comuni demo:", [t[1] for t in top])

    for t in ["comune", "incendio_storico", "pericolo_aib", "utente"]:
        cur.execute(f"SELECT count(*) FROM {t}")
        print(t, cur.fetchone()[0])
    cur.execute("SELECT count(*) FROM incendio_storico WHERE anno = 2025")
    print("incendi 2025:", cur.fetchone()[0])
    cur.execute("SELECT count(*) FROM incendio_storico WHERE data IS NULL OR ettari_totali IS NULL OR comune IS NULL")
    print("incendi con data/ettari/comune mancanti:", cur.fetchone()[0])
    cur.execute("SELECT classe, count(*) FROM pericolo_aib GROUP BY 1")
    print("classi pericolo:", cur.fetchall())
