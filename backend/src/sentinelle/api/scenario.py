from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import aree_critiche, incendi_attivi, invasi, rischio_oggi, simulazione
from ..db import engine

router = APIRouter()


class Richiesta(BaseModel):
    lat: float
    lon: float
    ore: int = Field(24, ge=1, le=24)
    area: dict | None = None  # GeoJSON: tutte le celle dentro partono a t=0


@router.get("/rischio/griglia")
def rischio_griglia():
    return rischio_oggi.griglia()


@router.post("/simulazione")
def simula(r: Richiesta):
    return simulazione.simula(r.lat, r.lon, r.ore, r.area)


@router.get("/invasi")
def lista_invasi():
    with engine.connect() as c:
        return invasi.geojson(c)


@router.get("/aree-critiche")
def lista_aree_critiche():
    return aree_critiche.aree_critiche()


@router.get("/incendi-attivi")
def lista_incendi_attivi():
    return incendi_attivi.incendi_attivi()
