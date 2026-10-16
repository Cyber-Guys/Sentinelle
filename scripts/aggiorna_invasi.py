"""Rigenera dati/invasi.json: volumi degli invasi sardi da sardegnacedoc.it/invasi/volumi.

La pagina scaricata e' dato non fidato: se ne estraggono solo numeri e nomi della tabella.
Coordinate: centro del bacino da OpenStreetMap/Nominatim (ottobre 2026); `coord_incerta`
segna quelle stimate a mano dove Nominatim non trovava il lago.
Uso: ./scripts/python.sh scripts/aggiorna_invasi.py
"""
import html
import json
import re
import urllib.request
from pathlib import Path

URL = "https://www.sardegnacedoc.it/invasi/volumi"
# numero d'ordine nella tabella CeDoc -> (nome breve, lat, lon, incerta)
COORD = {
    1: ("Flumineddu (Capanna Silicheri)", 39.83, 9.39, True),
    2: ("Lago del Flumendosa (Nuraghe Arrubiu)", 39.7244, 9.2659, False),
    3: ("Lago Mulargia (Monte su Rei)", 39.6182, 9.2484, False),
    4: ("Sa Forada de S'Acqua", 39.5375, 8.9712, False),
    5: ("Casa Fiume", 39.45, 9.36, True),
    6: ("Lago di Monte Arbus (Rio Leni)", 39.48, 8.67, True),
    7: ("Lago del Cixerri (Genna Is Abis)", 39.27, 8.79, True),
    8: ("Corongiu", 39.2231, 9.2786, True),
    9: ("Simbirizzi", 39.255, 9.215, True),
    10: ("Lago di Bau Pressiu", 39.1858, 8.7666, False),
    11: ("Lago di Is Barrocus", 39.7554, 9.0951, False),
    12: ("Lago di Monte Pranu", 39.0989, 8.6023, False),
    13: ("Crabosu (Rio Torrei)", 39.25, 8.62, True),
    14: ("Lago Omodeo (Cantoniera)", 40.0844, 8.8820, False),
    15: ("Lago Sos Canales", 40.5554, 9.3146, False),
    16: ("Lago di Pattada (Monte Lerno)", 40.5806, 9.1647, False),
    17: ("Lago Bidighinzu", 40.5468, 8.6745, False),
    18: ("Lago del Cuga", 40.6119, 8.4632, False),
    19: ("Lago del Temo (Monteleone Roccadoria)", 40.45, 8.58, True),
    20: ("Lago del Liscia", 40.9875, 9.2716, False),
    21: ("Lago Maccheronis (Posada)", 40.6346, 9.5973, False),
    22: ("Lago del Cedrino (Pedra 'e Othoni)", 40.3079, 9.5410, False),
    23: ("Lago Alto Flumendosa (Bau Muggeris)", 39.9426, 9.4466, False),
    24: ("Lago di Santa Lucia", 39.9659, 9.5939, False),
    25: ("Lago di Punta Gennarta", 39.3281, 8.5451, False),
    26: ("Lago di Medau Zirimilis", 39.2324, 8.8260, False),
    27: ("Lago di Gusana", 40.1261, 9.2067, False),
    28: ("Lago di Cucchinadorza", 40.1221, 9.1372, False),
    29: ("Lago Benzone", 40.1379, 9.0369, False),
    30: ("Lago del Coghinas (Muzzone)", 40.80, 9.05, True),
    31: ("Lago di Casteldoria", 40.8692, 8.8968, False),
    32: ("Lago di Olai", 40.1442, 9.3356, False),
    33: ("Lago di Govossai", 40.1240, 9.2845, False),
}


def celle(riga: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
            for c in re.findall(r"<t[dh][^>]*>.*?</t[dh]>", riga, flags=re.S)]


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (sentinelle-hackathon)"})
    pagina = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    righe = [celle(r) for r in re.findall(r"<tr.*?</tr>", pagina, flags=re.S)]
    data = re.search(r"\((\d{2})-(\d{4})\)", next(" ".join(r) for r in righe if any("Situazione" in c for c in r)))
    mese = f"{data.group(2)}-{data.group(1)}"
    invasi = []
    for r in righe:
        if len(r) < 5 or not r[0].isdigit() or int(r[0]) not in COORD:
            continue
        nome, lat, lon, incerta = COORD[int(r[0])]
        cap, vol = float(r[2]), float(r[3])
        invasi.append({"nome": nome, "nome_fonte": r[1], "lat": lat, "lon": lon, "coord_incerta": incerta,
                       "capacita_mm3": cap, "volume_mm3": vol, "riempimento": round(100 * vol / cap) if cap else 0})
    assert len(invasi) >= 30, f"tabella inattesa: {len(invasi)} invasi"
    out = {"fonte": "CeDoc Regione Sardegna, sardegnacedoc.it",
           "url": URL, "data_dato": mese, "unita": "Mm3", "invasi": invasi}
    dest = Path(__file__).resolve().parent.parent / "dati" / "invasi.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(invasi)} invasi, dato {mese} -> {dest}")


if __name__ == "__main__":
    main()
