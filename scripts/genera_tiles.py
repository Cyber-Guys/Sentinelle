"""Genera frontend/public/tiles/storico.pmtiles dai perimetri storici (dati/perimetri_*.geojson).

Richiede tippecanoe nel PATH (brew install tippecanoe, oppure conda-forge).
Proprieta' per feature: anno (int), data (AAAA-MM-GG|null), comune, ettari, bosco_ha.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from campi_incendi import comune, data_incendio, ettari_bosco, ettari_totali

RADICE = Path(__file__).resolve().parent.parent
USCITA = RADICE / "frontend" / "public" / "tiles" / "storico.pmtiles"


def _2d(g):
    if isinstance(g, list):
        return [_2d(x) for x in g] if g and isinstance(g[0], list) else g[:2]
    return g


def main():
    if not shutil.which("tippecanoe"):
        raise SystemExit("tippecanoe non trovato nel PATH")
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        seq = Path(tmp) / "incendi.geojsonl"
        n = 0
        with seq.open("w") as out:
            for anno in range(2005, 2026):
                path = RADICE / "dati" / f"perimetri_{anno}.geojson"
                if not path.exists():
                    print("manca", anno)
                    continue
                for f in json.loads(path.read_text())["features"]:
                    g = f.get("geometry")
                    if not g or "coordinates" not in g:
                        continue
                    p = f["properties"]
                    d = data_incendio(p)
                    out.write(json.dumps({"type": "Feature", "geometry": {"type": g["type"], "coordinates": _2d(g["coordinates"])},
                        "properties": {"anno": anno, "data": d.isoformat() if d else None, "comune": comune(p),
                                       "ettari": ettari_totali(p), "bosco_ha": ettari_bosco(p)}}) + "\n")
                    n += 1
        print(n, "feature")
        subprocess.run(["tippecanoe", "-o", str(USCITA), "-l", "incendi", "-zg", "--minimum-zoom=6",
                        "--drop-densest-as-needed", "--extend-zooms-if-still-dropping", "--force", "--no-progress-indicator", str(seq)], check=True)
    print(USCITA, round(USCITA.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
