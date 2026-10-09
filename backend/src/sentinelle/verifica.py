import math
import tomllib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from sqlalchemy import text

from .config import FILE_PESI
from .fonti import Meteo, classe_suolo, hotspot_sardegna, meteo
from .rischio import rischio_meteo

PESI = tomllib.loads(FILE_PESI.read_text())
PERICOLO = {"Basso": 0.0, "Mediobasso": 0.25, "Medio": 0.5, "Medioalto": 0.75, "Alto": 1.0}


@dataclass(frozen=True)
class Contesto:
    hotspot_km: float | None          # None = fonte non disponibile
    meteo: Meteo | None
    classe_suolo: tuple[int, str] | None
    pericolo_aib: str | None          # None = fuori layer
    segnalazioni_vicine: int          # entro 2 km, ultima ora
    incendi_storici: int              # entro 1 km, 2005-2025


@dataclass(frozen=True)
class Esito:
    priorita: int
    motivazioni: list[str]
    fattori: list[dict] = field(default_factory=list)


ETICHETTE = {"hotspot": "Hotspot satellitare", "meteo": "Meteo", "suolo": "Uso del suolo",
             "pericolo": "Pericolo regionale", "vicine": "Segnalazioni vicine", "storico": "Incendi storici"}
CLASSI_PERICOLO = {"Basso": "basso", "Mediobasso": "medio-basso", "Medio": "medio",
                   "Medioalto": "medio-alto", "Alto": "alto"}


def _virgola(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def _vegetazione(codice: int) -> float:
    if codice in (311, 312, 313, 322, 323, 324):
        return 1.0
    if codice in (321, 333):
        return 0.8
    if codice in (241, 242, 243, 244):
        return 0.5
    if 200 <= codice < 300:
        return 0.3
    if codice < 200:
        return 0.1
    return 0.0


def _vicine(n: int) -> str:
    if n == 0:
        return "Nessun'altra segnalazione entro 2 km nell'ultima ora"
    if n == 1:
        return "1 altra segnalazione entro 2 km nell'ultima ora"
    return f"{n} altre segnalazioni entro 2 km nell'ultima ora"


def _storici(n: int) -> str:
    if n == 0:
        return "Nessun incendio storico entro 1 km (2005-2025)"
    if n == 1:
        return "1 incendio storico entro 1 km (2005-2025)"
    return f"{n} incendi storici entro 1 km (2005-2025)"


def calcola_priorita(c: Contesto, pesi: dict[str, float]) -> Esito:
    termini: list[tuple[str, float | None, str]] = []  # (chiave, valore 0..1 o None, testo del valore)

    if c.hotspot_km is None:
        termini.append(("hotspot", None, "Satellite non disponibile"))
    elif c.hotspot_km > 10:
        termini.append(("hotspot", 0.0, "Nessun hotspot satellitare entro 10 km"))
    else:
        termini.append(("hotspot", 1 - c.hotspot_km / 10, f"Hotspot satellitare a {_virgola(c.hotspot_km)} km"))

    if c.meteo is None:
        termini.append(("meteo", None, "Meteo non disponibile"))
    else:
        m = c.meteo
        g = m.giorni_senza_pioggia
        pioggia = "pioggia recente" if g == 0 else "1 giorno senza pioggia" if g == 1 else f"{g} giorni senza pioggia"
        termini.append(("meteo", rischio_meteo(m),
                        f"Raffiche {m.raffiche_kmh:.0f} km/h · umidità {m.umidita:.0f}% · {pioggia}"))

    if c.classe_suolo is None:
        termini.append(("suolo", None, "Uso del suolo non disponibile"))
    else:
        codice, desc = c.classe_suolo
        termini.append(("suolo", _vegetazione(codice), desc[:1].upper() + desc[1:]))

    if c.pericolo_aib is None:
        termini.append(("pericolo", 0.0, "Fuori dalle zone di pericolo AIB"))
    else:
        classe = CLASSI_PERICOLO.get(c.pericolo_aib, c.pericolo_aib.lower())
        termini.append(("pericolo", PERICOLO.get(c.pericolo_aib, 0.0), f"{classe[:1].upper()}{classe[1:]} · carta del pericolo AIB"))

    termini.append(("vicine", min(c.segnalazioni_vicine / 3, 1.0), _vicine(c.segnalazioni_vicine)))
    termini.append(("storico", min(c.incendi_storici / 5, 1.0), _storici(c.incendi_storici)))

    somma_pesi = sum(pesi[n] for n, v, _ in termini if v is not None)
    fattori, motivazioni = [], []
    for n, v, testo in termini:
        peso = pesi[n] / somma_pesi if v is not None and somma_pesi else 0.0
        fattori.append({"chiave": n, "etichetta": ETICHETTE[n], "valore": round(v or 0.0, 3),
                        "peso": round(peso, 4), "contributo": round(100 * peso * (v or 0.0), 1),
                        "testo": testo, "disponibile": v is not None})
        if n == "meteo" and v is not None:
            motivazioni.append(f"Meteo: {testo[0].lower()}{testo[1:]}")
        elif n == "suolo" and v is not None:
            motivazioni.append(f"Uso del suolo: {testo[0].lower()}{testo[1:]}")
        elif n == "pericolo" and c.pericolo_aib is not None:
            motivazioni.append(f"Pericolo regionale: {CLASSI_PERICOLO.get(c.pericolo_aib, c.pericolo_aib.lower())}")
        else:
            motivazioni.append(testo)
    punteggio = sum(pesi[n] * v for n, v, _ in termini if v is not None) / somma_pesi if somma_pesi else 0.0
    return Esito(round(100 * punteggio), motivazioni, fattori)


def _distanza_km(lat1, lon1, lat2, lon2) -> float:
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def raccogli_contesto(sessione, lat: float, lon: float) -> Contesto:
    # fonti esterne in parallelo (rete), mentre il thread corrente fa le query al DB
    with ThreadPoolExecutor(3) as pool:
        f_hs = pool.submit(hotspot_sardegna)
        f_meteo = pool.submit(meteo, lat, lon)
        f_suolo = pool.submit(classe_suolo, lat, lon)
        return _contesto_db(sessione, lat, lon, f_hs, f_meteo, f_suolo)


def _contesto_db(sessione, lat, lon, f_hs, f_meteo, f_suolo) -> Contesto:
    # prefiltro con indice GIST (&& + ST_Expand), poi distanza esatta su geography
    p = {"lon": lon, "lat": lat}
    punto = "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)"
    classe = sessione.execute(text(
        f"SELECT classe FROM pericolo_aib WHERE ST_Intersects(geom, {punto}) LIMIT 1"), p).scalar()
    vicine = sessione.execute(text(
        f"SELECT count(*) FROM segnalazione WHERE geom && ST_Expand({punto}, 0.05) "
        f"AND ST_DWithin(geom::geography, {punto}::geography, 2000) "
        "AND stato <> 'archiviata' AND creata_il > now() - interval '1 hour'"), p).scalar()
    storici = sessione.execute(text(
        f"SELECT count(*) FROM incendio_storico WHERE geom && ST_Expand({punto}, 0.05) "
        f"AND ST_DWithin(geom::geography, {punto}::geography, 1000) AND anno BETWEEN 2005 AND 2025"), p).scalar()
    hs = f_hs.result()
    hotspot_km = None if hs is None else min((_distanza_km(lat, lon, h.lat, h.lon) for h in hs), default=999.0)
    return Contesto(hotspot_km, f_meteo.result(), f_suolo.result(), classe, vicine, storici)
