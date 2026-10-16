import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from . import eventi
from .api import gioco as api_gioco
from .api import cittadino, scenario, segnalazioni, storico
from .config import impostazioni
from .db import engine
from .gioco import prepara_db
from .invasi import carica as carica_invasi
from .basi import carica as carica_basi
from . import flotta


@asynccontextmanager
async def ciclo_vita(_):
    # Il database puo' essere ancora in avvio (docker compose appena lanciato): si aspetta fino a 60 s.
    for tentativo in range(30):
        try:
            with engine.begin() as conn:  # tabelle e missioni del gioco (idempotente)
                prepara_db(conn)
                carica_invasi(conn)
                carica_basi(conn)
            break
        except OperationalError:
            if tentativo == 29:
                raise
            await asyncio.sleep(2)
    def scalda_flotta():  # la sagoma dell'isola per i mezzi di terra costa qualche secondo: si calcola subito
        with engine.connect() as conn:
            flotta.stato(conn, 0)
    compiti = [asyncio.create_task(asyncio.to_thread(scalda_flotta)), asyncio.create_task(eventi.ascolta()), asyncio.create_task(eventi.controlla_hotspot())]
    yield
    for c in compiti:
        c.cancel()


app = FastAPI(title="Sentinelle", lifespan=ciclo_vita)
app.add_middleware(CORSMiddleware, allow_origins=impostazioni.cors_origini,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(storico.router)
app.include_router(segnalazioni.router)
app.include_router(api_gioco.router)
app.include_router(eventi.router)
app.include_router(scenario.router)
app.include_router(cittadino.router)


@app.get("/salute")
def salute():
    return {"ok": True}
