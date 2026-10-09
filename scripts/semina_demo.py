"""Semina dati di demo SIMULATI per la classifica: 20 utenti su 6 comuni, con punti e missioni 'posizione'.
Idempotente: cancella solo gli utenti il cui nome termina con "(demo)". Gli utenti base restano."""
import math
import os
import random
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))
from sentinelle.gioco import prepara_db  # noqa: E402

URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://sentinelle:sentinelle@localhost:5432/sentinelle")
NOMI = ["Anna", "Bruno", "Chiara", "Davide", "Edoardo", "Francesca", "Gianni", "Hilary", "Ilaria", "Jacopo",
        "Katia", "Lorenzo", "Martina", "Nicola", "Ornella", "Paolo", "Rita", "Salvatore", "Tiziana", "Valerio"]
RAGGIO_M = 3000
rng = random.Random(2025)  # seed fisso: stesso risultato a ogni esecuzione

with create_engine(URL).begin() as c:
    prepara_db(c)
    c.execute(text("DELETE FROM missione_completata WHERE utente_id IN (SELECT id FROM utente WHERE nome LIKE '%(demo)')"))
    c.execute(text("DELETE FROM utente WHERE nome LIKE '%(demo)'"))
    comuni = c.execute(text(
        "SELECT co.id, co.nome, ST_Y(ST_PointOnSurface(co.geom)) AS lat, ST_X(ST_PointOnSurface(co.geom)) AS lon "
        "FROM incendio_storico i JOIN comune co ON co.nome = i.comune GROUP BY co.id, co.nome, co.geom "
        "ORDER BY count(*) DESC, co.nome LIMIT 6")).all()
    posizione = c.execute(text("SELECT id, punti FROM missione WHERE tipo = 'posizione' ORDER BY id")).all()

    for i, nome in enumerate(NOMI):
        co = comuni[i % len(comuni)]
        punti = 0
        uid = c.execute(text("INSERT INTO utente (nome, comune_id) VALUES (:n, :c) RETURNING id"),
                        {"n": f"{nome} (demo)", "c": co.id}).scalar()
        for _ in range(rng.randint(1, 8)):  # missioni di mappatura entro 3 km dal comune
            m = rng.choice(posizione)
            d, a = RAGGIO_M * math.sqrt(rng.random()), rng.uniform(0, 2 * math.pi)
            lat = co.lat + d * math.cos(a) / 111320
            lon = co.lon + d * math.sin(a) / (111320 * math.cos(math.radians(co.lat)))
            c.execute(text("INSERT INTO missione_completata (utente_id, missione_id, punti, geom, completata_il) VALUES "
                           "(:u, :m, :p, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), now() - make_interval(days => :g))"),
                      {"u": uid, "m": m.id, "p": m.punti, "lon": lon, "lat": lat, "g": rng.randint(0, 20)})
            punti += m.punti
        punti += rng.choice([0, 10, 50, 100, 150, 250, 400])  # quiz, segnalazioni confermate, ecc.
        c.execute(text("UPDATE utente SET punti = :p WHERE id = :u"), {"p": punti, "u": uid})

    print("comuni demo:", [co.nome for co in comuni])
    for r in c.execute(text(
            "SELECT co.nome AS comune, sum(u.punti) AS punti, count(*) FILTER (WHERE u.punti > 0) AS utenti "
            "FROM utente u JOIN comune co ON co.id = u.comune_id GROUP BY co.nome HAVING sum(u.punti) > 0 "
            "ORDER BY 2 DESC LIMIT 20")):
        print(f"  {r.comune:<22} {int(r.punti):>5} punti  {r.utenti} utenti")
