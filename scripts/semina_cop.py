"""Segnalazioni dimostrative per la vista Segnalazioni della dashboard COP (piano 2026-10-17-dashboard-cop).

SIMULATE: gruppi di segnalazioni vicine con foto (dati/demo_foto, licenze in CREDITI.md), conferme e smentite
di altri utenti nel raggio. Idempotente: cancella solo cio' che ha creato (utenti "(demo-cop)").
Uso: ./scripts/docker.sh exec backend python scripts/semina_cop.py
"""
import math
import random
import shutil
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "backend" / "src"))
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from sentinelle.api.segnalazioni import aggiorna_priorita  # noqa: E402
from sentinelle.config import DIR_FOTO  # noqa: E402
from sentinelle.db import engine  # noqa: E402

FOTO = RADICE / "dati" / "demo_foto"
rng = random.Random(1707)

# luogo, lat, lon, minuti fa, [(tipo, foto, nota)], conferme, smentite
GRUPPI = [
    ("Settimo San Pietro, Monte Cresia", 39.300, 9.190, 14,
     [("fuoco", "fiamme-1.jpg", "Fiamme alte sulla collina dietro le case"),
      ("fuoco", "fiamme-2.jpg", None), ("fumo", "fumo-2.jpg", "Colonna di fumo scuro verso est")], 7, 0),
    ("Capoterra, Poggio dei Pini", 39.165, 8.985, 32,
     [("fumo", "cagliari-2.jpg", "Fumo grigio sopra le colline"), ("fumo", "cagliari-1.jpg", "Visto dal porto")], 3, 1),
    ("Burcei", 39.343, 9.360, 9, [("fuoco", "barbecue.jpg", "Fuoco nel bosco")], 0, 2),
    ("Bosa, Monte Furru", 40.290, 8.520, 21,
     [("fuoco", "fiamme-3.jpg", "Fronte di fiamma sul versante"), ("fumo", "fumo-3.jpg", None)], 4, 0),
    ("Alghero, Monte Doglia", 40.600, 8.240, 47, [("fumo", "fumo-1.jpg", "Fumo all'orizzonte")], 1, 0),
    ("Dorgali, Cala Gonone", 40.283, 9.620, 6, [("fuoco", None, "Vedo un bagliore sulla strada per Cala Gonone")], 2, 0),
]


def fattori(rischio: float) -> list[dict]:
    voci = [("hotspot", "Hotspot satellitare", 0.3, rng.uniform(0, 0.5), "Nessun hotspot entro 5 km"),
            ("meteo", "Meteo", 0.25, rng.uniform(0.4, 0.8), "Raffiche 28 km/h · umidità 31% · 18 giorni senza pioggia"),
            ("suolo", "Uso del suolo", 0.15, rng.uniform(0.5, 0.9), "Macchia mediterranea"),
            ("pericolo", "Pericolo regionale", 0.1, rischio, "Bollettino CFD: pericolo alto" if rischio > 0.7 else "Bollettino CFD: pericolo medio"),
            ("storico", "Incendi storici", 0.1, rng.uniform(0.3, 1), f"{rng.randint(3, 30)} incendi storici entro 1 km (2005-2025)")]
    return [{"chiave": k, "etichetta": e, "peso": p, "valore": round(v, 3), "contributo": round(p * v * 100, 1),
             "testo": t, "disponibile": True} for k, e, p, v, t in voci]


def punto_vicino(lat, lon, m):
    d, a = m * math.sqrt(rng.random()), rng.uniform(0, 2 * math.pi)
    return lat + d * math.cos(a) / 111320, lon + d * math.sin(a) / (111320 * math.cos(math.radians(lat)))


with Session(engine) as s:
    vecchi = "SELECT id FROM utente WHERE nome LIKE '%(demo-cop)'"
    s.execute(text(f"DELETE FROM voto_segnalazione WHERE utente_id IN ({vecchi}) OR segnalazione_id IN "
                   f"(SELECT id FROM segnalazione WHERE utente_id IN ({vecchi}))"))
    s.execute(text(f"DELETE FROM segnalazione WHERE utente_id IN ({vecchi})"))
    s.execute(text(f"DELETE FROM utente WHERE id IN ({vecchi})"))
    DIR_FOTO.mkdir(exist_ok=True)
    n_utente, totale = 0, 0

    def utente():
        global n_utente
        n_utente += 1
        return s.execute(text("INSERT INTO utente (nome) VALUES (:n) RETURNING id"), {"n": f"Sentinella {n_utente} (demo-cop)"}).scalar()

    for luogo, lat, lon, minuti, segn, conferme, smentite in GRUPPI:
        rischio = rng.uniform(0.6, 0.95)
        for k, (tipo, foto, nota) in enumerate(segn):
            if foto:
                shutil.copy(FOTO / foto, DIR_FOTO / f"demo-cop-{foto}")
            la, lo = punto_vicino(lat, lon, 600)
            fa = fattori(rischio)
            id = s.execute(text(
                "INSERT INTO segnalazione (utente_id, tipo, geom, foto, nota, priorita, motivazioni, fattori, creata_il, aggiornata_il) "
                "VALUES (:u, :t, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :f, :n, :p, CAST(:m AS jsonb), CAST(:fa AS jsonb), "
                "now() - make_interval(mins => :min), now() - make_interval(mins => :min)) RETURNING id"),
                {"u": utente(), "t": tipo, "lo": lo, "la": la, "f": f"demo-cop-{foto}" if foto else None, "n": nota,
                 "p": round(sum(f["contributo"] for f in fa)), "m": __import__("json").dumps([f["testo"] for f in fa]),
                 "fa": __import__("json").dumps(fa), "min": minuti - k * 3}).scalar()
            if k == 0:  # conferme e smentite dei vicini sulla prima segnalazione del gruppo
                for voto, quanti in (("ancora", conferme), ("finito", smentite)):
                    for _ in range(quanti):
                        vla, vlo = punto_vicino(la, lo, 1500)
                        s.execute(text("INSERT INTO voto_segnalazione (segnalazione_id, utente_id, voto, geom, creato_il) VALUES "
                                       "(:i, :u, :v, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), now() - make_interval(mins => :m))"),
                                  {"i": id, "u": utente(), "v": voto, "lo": vlo, "la": vla, "m": rng.randint(1, max(minuti - 1, 1))})
            aggiorna_priorita(s, id)
            totale += 1
    s.commit()
    print(f"{totale} segnalazioni demo in {len(GRUPPI)} gruppi, {n_utente} utenti (demo-cop)")
