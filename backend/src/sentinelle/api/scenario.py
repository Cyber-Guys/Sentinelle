from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import invasi, rischio_oggi, simulazione
from ..db import engine

router = APIRouter()


class Richiesta(BaseModel):
    lat: float
    lon: float
    ore: int = Field(24, ge=1, le=24)


@router.get("/rischio/griglia")
def rischio_griglia():
    return rischio_oggi.griglia()


@router.post("/simulazione")
def simula(r: Richiesta):
    return simulazione.simula(r.lat, r.lon, r.ore)


@router.get("/invasi")
def lista_invasi():
    with engine.connect() as c:
        return invasi.geojson(c)
