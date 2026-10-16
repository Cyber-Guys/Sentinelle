"""Rigenera dati/basi.json: basi operative antincendio in Sardegna da fonti aperte.

- Vigili del Fuoco e stazioni del Corpo Forestale: OpenStreetMap (Overpass), comune via Nominatim reverse.
- Servizi territoriali CFVA e basi elicotteri AIB regionali: elenco dai siti istituzionali
  (sardegnaambiente.it, Piano regionale AIB), geocodificati per localita' con Nominatim -> coord_incerta.
Uso: ./scripts/python.sh scripts/aggiorna_basi.py
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Sentinelle/0.1 (+https://github.com/Cyber-Guys/Sentinelle)"}
FILE = Path(__file__).resolve().parents[1] / "dati" / "basi.json"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
QUERY = ('[out:json][timeout:60];area["ISO3166-2"="IT-88"]->.s;'
         '(nwr["amenity"="fire_station"](area.s);nwr["amenity"~"police|ranger_station"]["operator"~"Forestale",i](area.s););out center tags;')
FONTE_CFVA = "Regione Sardegna, sardegnaambiente.it (Corpo Forestale, servizi territoriali)"
FONTE_AIB = "Regione Sardegna, Piano regionale AIB (basi elicotteri della flotta regionale)"
SERVIZI_CFVA = ["Cagliari", "Iglesias", "Lanusei", "Nuoro", "Oristano", "Sassari", "Tempio Pausania"]
# (nome base, localita' da geocodificare)
BASI_AIB = [("Alà dei Sardi", "Alà dei Sardi"), ("Anela", "Anela"), ("Bosa", "Bosa"),
            ("Farcana", "Farcana, Nuoro"), ("Fenosu", "Aeroporto di Oristano-Fenosu"),
            ("Limbara", "Monte Limbara, Tempio Pausania"), ("Marganai", "Marganai, Iglesias"),
            ("Pula", "Pula, Sardegna"), ("San Cosimo", "Lanusei"), ("Sorgono", "Sorgono"),
            ("Villasalto", "Villasalto")]


def http(url: str, dati: bytes | None = None) -> dict | list:
    req = urllib.request.Request(url, data=dati, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def overpass() -> list:
    for tentativo in range(4):
        try:
            return http(OVERPASS[tentativo % 2], urllib.parse.urlencode({"data": QUERY}).encode())["elements"]
        except Exception as e:  # noqa: BLE001
            print("Overpass non risponde, riprovo:", e)
            time.sleep(5)
    return []


def nominatim(q: str, citta: bool = False) -> dict | None:
    time.sleep(1.1)  # policy Nominatim: max 1 richiesta al secondo
    p = {"city": q, "state": "Sardegna"} if citta else {"q": q}  # citta': il comune, non la provincia omonima
    r = http("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {**p, "format": "json", "limit": 1, "countrycodes": "it", "addressdetails": 1}))
    return r[0] if r else None


def comune(lat: float, lon: float) -> str:
    time.sleep(1.1)
    a = http("https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode(
        {"lat": lat, "lon": lon, "format": "json", "zoom": 10})).get("address", {})
    return italiano(a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or "")


def italiano(n: str) -> str:
    """Nominatim restituisce i toponimi bilingui ("Casteddu/Cagliari"): si tiene la forma italiana."""
    return n.split("/")[-1].strip()


def indirizzo(t: dict) -> str:
    return " ".join(x for x in (t.get("addr:street"), t.get("addr:housenumber")) if x)


def main() -> None:
    basi = []
    elementi = overpass()
    for e in elementi:
        t = e.get("tags", {})
        lat, lon = (e["lat"], e["lon"]) if "lat" in e else (e["center"]["lat"], e["center"]["lon"])
        forestale = "forestal" in (t.get("operator", "") + t.get("name", "")).lower()
        if forestale and any(x in t.get("name", "").lower() for x in ("vedetta", "ente foreste")):
            continue
        com = italiano(t.get("addr:city") or comune(lat, lon))
        nome = t.get("name") or ""
        if forestale:
            ente = "CFVA"
            nome = f"Stazione forestale di {com}" if not nome or nome.lower().startswith(("corpo", "stazione forestale")) else nome
        else:
            ente = "VVF"
            n = nome.lower()
            if not nome or n in ("vigili del fuoco", "vigili del fuoco ", "caserma vvff"):
                nome = f"Vigili del Fuoco · {com}"
        basi.append({"id": f"osm-{e['type'][0]}{e['id']}", "nome": nome, "ente": ente, "tipo": "comando" if "comando" in nome.lower() else "distaccamento" if ente == "VVF" else "stazione",
                     "comune": com, "indirizzo": indirizzo(t), "lat": round(lat, 5), "lon": round(lon, 5),
                     "coord_incerta": False, "fonte": f"OpenStreetMap ({e['type']} {e['id']}), ODbL"})
    for c in SERVIZI_CFVA:
        r = nominatim(c, citta=True)
        if r:
            basi.append({"id": f"cfva-st-{c.lower().replace(' ', '-')}", "nome": f"Servizio territoriale CFVA di {c}", "ente": "CFVA", "tipo": "servizio territoriale",
                         "comune": c, "indirizzo": "", "lat": round(float(r["lat"]), 5), "lon": round(float(r["lon"]), 5),
                         "coord_incerta": True, "fonte": FONTE_CFVA})
    for nome, q in BASI_AIB:
        r = nominatim(q)
        if r:
            a = r.get("address", {})
            com = italiano(a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or nome)
            basi.append({"id": f"aib-{nome.lower().replace(' ', '-').replace('à', 'a')}", "nome": f"Base elicotteri AIB {nome}", "ente": "AIB", "tipo": "base elicotteri",
                         "comune": com, "indirizzo": "", "lat": round(float(r["lat"]), 5), "lon": round(float(r["lon"]), 5),
                         "coord_incerta": True, "fonte": FONTE_AIB})
    r = nominatim("Aeroporto di Olbia Costa Smeralda")
    if r:
        basi.append({"id": "aib-olbia-canadair", "nome": "Base Canadair Olbia (COAU, schieramento estivo)", "ente": "AIB", "tipo": "base Canadair",
                     "comune": "Olbia", "indirizzo": "Aeroporto Costa Smeralda", "lat": round(float(r["lat"]), 5), "lon": round(float(r["lon"]), 5),
                     "coord_incerta": True, "fonte": "Dipartimento Protezione Civile, COAU (schieramento flotta aerea dello Stato)"})
    FILE.write_text(json.dumps({"aggiornato_il": time.strftime("%Y-%m-%d"), "basi": basi}, ensure_ascii=False, indent=1))
    conti = {}
    for b in basi:
        conti[b["ente"]] = conti.get(b["ente"], 0) + 1
    print(FILE, conti)


if __name__ == "__main__":
    main()
