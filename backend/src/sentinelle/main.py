from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import gioco as api_gioco
from .api import segnalazioni, storico
from .config import impostazioni
from .db import engine
from .gioco import prepara_db


@asynccontextmanager
async def ciclo_vita(_):
    with engine.begin() as conn:  # tabelle e missioni del gioco (idempotente)
        prepara_db(conn)
    yield


app = FastAPI(title="Sentinelle", lifespan=ciclo_vita)
app.add_middleware(CORSMiddleware, allow_origins=impostazioni.cors_origini,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(storico.router)
app.include_router(segnalazioni.router)
app.include_router(api_gioco.router)


@app.get("/salute")
def salute():
    return {"ok": True}
