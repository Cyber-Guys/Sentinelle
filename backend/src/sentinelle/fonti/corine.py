import json
import math

from ..config import DIR_OFFLINE, impostazioni
from .cache import con_cache
from .http import client

URL = "https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/identify"

# Le risposte identify portano solo il codice: descrizioni dei codici principali.
DESCRIZIONI = {
    111: "Tessuto urbano continuo", 112: "Tessuto urbano discontinuo",
    121: "Aree industriali o commerciali", 122: "Reti stradali e ferroviarie", 123: "Aree portuali",
    124: "Aeroporti", 131: "Aree estrattive", 132: "Discariche", 133: "Cantieri",
    141: "Aree verdi urbane", 142: "Aree sportive e ricreative",
    211: "Seminativi in aree non irrigue", 212: "Seminativi in aree irrigue", 213: "Risaie",
    221: "Vigneti", 222: "Frutteti", 223: "Oliveti", 231: "Prati stabili",
    241: "Colture annuali associate a permanenti", 242: "Sistemi colturali complessi",
    243: "Colture agrarie con spazi naturali", 244: "Aree agroforestali",
    311: "Boschi di latifoglie", 312: "Boschi di conifere", 313: "Boschi misti",
    321: "Pascoli naturali e praterie", 322: "Brughiere e cespuglieti", 323: "Vegetazione sclerofilla",
    324: "Boscaglia in evoluzione", 331: "Spiagge e dune", 332: "Rocce nude",
    333: "Vegetazione rada", 334: "Aree percorse da incendio", 335: "Ghiacciai e nevi perenni",
    411: "Paludi interne", 412: "Torbiere", 421: "Paludi salmastre", 422: "Saline", 423: "Zone intertidali",
    511: "Corsi d'acqua", 512: "Bacini d'acqua", 521: "Lagune", 522: "Estuari", 523: "Mari e oceani",
}


def _a_3857(lat: float, lon: float) -> tuple[float, float]:
    r = 6378137.0
    return r * math.radians(lon), r * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def _interroga(lat: float, lon: float) -> tuple[int, str] | None:
    if impostazioni.modalita_offline:
        dati = json.loads((DIR_OFFLINE / "corine.json").read_text())
    else:
        x, y = _a_3857(lat, lon)
        r = client.get(URL, params={
            "f": "json", "geometry": f"{x},{y}", "geometryType": "esriGeometryPoint", "sr": 102100,
            "layers": "all", "tolerance": 1, "returnGeometry": "false",
            "mapExtent": f"{x - 500},{y - 500},{x + 500},{y + 500}", "imageDisplay": "400,400,96"})
        r.raise_for_status()
        dati = r.json()
    ris = dati.get("results") or []
    if not ris:
        raise ValueError("nessun risultato Corine")  # niente cache su risposta vuota
    codice = int(ris[0]["attributes"]["Code_18"])
    return codice, DESCRIZIONI.get(codice, f"CLC {codice}")


def classe_suolo(lat: float, lon: float) -> tuple[int, str] | None:
    return con_cache(f"corine:{lat:.4f}:{lon:.4f}", lambda: _interroga(lat, lon))
