"""Affidabilita' delle segnalazioni condivise: funzioni pure (pesi in config/pesi.toml [affidabilita])."""
import tomllib
from dataclasses import dataclass, field

from .config import FILE_PESI

CONF = tomllib.loads(FILE_PESI.read_text())["affidabilita"]
FUOCO = ("fuoco", "fumo")


@dataclass(frozen=True)
class Voto:
    voto: str          # 'ancora' | 'finito' (l'autore conta come 'ancora')
    peso: float        # affidabilita' di chi vota
    eta_min: float


@dataclass(frozen=True)
class Prove:
    hotspot: bool = False
    foto: bool = False
    rischio_alto: bool = False
    operatore: bool = False   # confermata dall'operatore


@dataclass(frozen=True)
class Punteggio:
    valore: float
    livello: str       # da_verificare | probabile | comunita | operatori
    fattori: list[dict] = field(default_factory=list)


def affidabilita_utente(confermate: int, valutate: int) -> float:
    return (confermate + 1) / (valutate + 2)


def emivita_min(tipo: str, conf: dict = CONF) -> float:
    return conf["emivita_min_fuoco"] if tipo in FUOCO else conf["emivita_min_altri"]


def _decad(eta_min: float, emivita: float) -> float:
    return 0.5 ** (max(eta_min, 0.0) / emivita)


def punteggio(voti: list[Voto], prove: Prove, eta_min: float, tipo: str, conf: dict = CONF) -> Punteggio:
    em = emivita_min(tipo, conf)
    ancora = sum(v.peso * _decad(v.eta_min, em) for v in voti if v.voto == "ancora")
    finito = sum(v.peso * _decad(v.eta_min, em) for v in voti if v.voto == "finito")
    fattori = [{"chiave": "conferme", "etichetta": "Conferme", "contributo": round(ancora, 2)},
               {"chiave": "smentite", "etichetta": "Non c'e' piu'", "contributo": round(-finito, 2)}]
    d = _decad(eta_min, em)
    for chiave, etichetta, attiva in (("hotspot", "Hotspot satellitare entro 2 km", prove.hotspot),
                                      ("foto", "Foto", prove.foto),
                                      ("rischio_alto", "Zona a rischio alto", prove.rischio_alto)):
        if attiva:
            fattori.append({"chiave": chiave, "etichetta": etichetta,
                            "contributo": round(conf["bonus_" + chiave] * d, 2)})
    valore = round(sum(f["contributo"] for f in fattori), 2)
    if prove.operatore:
        livello = "operatori"
    elif valore >= conf["soglia_comunita"]:
        livello = "comunita"
    elif valore >= conf["soglia_probabile"]:
        livello = "probabile"
    else:
        livello = "da_verificare"
    return Punteggio(valore, livello, fattori)


def probabilmente_spento(voti: list[Voto], conf: dict = CONF) -> bool:
    f = conf["finestra_spento_min"]
    finito = sum(v.peso for v in voti if v.voto == "finito" and v.eta_min <= f)
    ancora = sum(v.peso for v in voti if v.voto == "ancora" and v.eta_min <= f)
    return finito > ancora
