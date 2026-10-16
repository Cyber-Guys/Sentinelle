from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import rischio_oggi, simulazione

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
