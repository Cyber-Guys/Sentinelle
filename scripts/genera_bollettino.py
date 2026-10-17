"""Genera i bollettini CFD SIMULATI della dashboard COP in dati/bollettini/ (piano 2026-10-17-dashboard-cop).

Il calcolo (buffer e smussatura delle zone su tutta l'isola) richiede ~10 s e molta RAM per giorno: si fa una volta
su un PC capiente, si committano i JSON e il backend li legge senza ricalcolare. Scrive anche aree-cop.json
(confini delle 7 aree COP), cosi' anche quelli non si ricalcolano all'avvio.

Uso (stack Docker acceso):  ./scripts/docker.sh bollettini [giorni] [AAAA-MM-GG di partenza]
Uso diretto:                python scripts/genera_bollettino.py --giorni 7 --da 2026-10-17 --out dati/bollettini
Guida: README.md, sezione "Bollettino CFD simulato"
"""
import argparse
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))
from sentinelle import cop  # noqa: E402

p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
p.add_argument("--giorni", type=int, default=7, help="quanti giorni generare (default 7)")
p.add_argument("--da", type=date.fromisoformat, default=date.today(), help="primo giorno, AAAA-MM-GG (default oggi)")
p.add_argument("--out", type=Path, default=cop.DIR_BOLLETTINI, help="cartella di destinazione")
p.add_argument("--forza", action="store_true", help="rigenera anche i giorni gia' presenti")
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=True)

t = time.time()
aree = cop.calcola_aree()
(a.out / "aree-cop.json").write_text(json.dumps(aree))
cop.aree.cache_clear()
cop.aree = lambda: aree  # le quote per area del bollettino usano questi confini
print(f"aree-cop.json: {len(aree['features'])} aree ({time.time() - t:.1f} s)")

for k in range(a.giorni):
    g = a.da + timedelta(days=k)
    f = a.out / f"bollettino-{g.isoformat()}.json"
    if f.exists() and not a.forza:
        print(f"{f.name}: gia' presente (--forza per rigenerare)")
        continue
    t = time.time()
    b = cop.calcola_bollettino(g)
    f.write_text(json.dumps(b))
    massimi = {aid: q["massimo"] for aid, q in b["per_area"].items()}
    print(f"{f.name}: {f.stat().st_size // 1024} KB, {time.time() - t:.1f} s, {massimi}")
print(f"Fatto: file in {a.out}")
