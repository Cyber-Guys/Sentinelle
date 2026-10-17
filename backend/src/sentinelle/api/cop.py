from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from .. import cop
from .segnalazioni import conferma

router = APIRouter(prefix="/cop")


@router.get("/aree")
def aree():
    return cop.aree()


@router.get("/bollettino")
def bollettino(giorno: str = "oggi"):
    return cop.bollettino(date.today() + timedelta(days=1 if giorno == "domani" else 0))


@router.get("/vedette")
def vedette():
    return cop.vedette()


@router.get("/fuochi")
def fuochi():
    return cop.fuochi(date.today())


@router.get("/incendi")
def incendi():
    return cop.incendi()


@router.post("/incendi/{id}/concludi")
def concludi(id: str):
    f = cop.concludi(id)
    if f is None:
        raise HTTPException(404, "incendio non trovato")
    return f


@router.get("/statistiche")
def statistiche(area: str):
    s = cop.statistiche(area)
    if not s:
        raise HTTPException(404, "area non trovata")
    return s


@router.post("/segnalazioni/{id}/certifica")
def certifica(id: int):
    """Conferma dell'operatore: l'app la mostra come incendio (livello "operatori") e avvisa chi e' vicino."""
    return {**conferma(id), "avvisati": cop.avvisati(id)}
