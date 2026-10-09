from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import segnalazioni, storico
from .config import impostazioni

app = FastAPI(title="Sentinelle")
app.add_middleware(CORSMiddleware, allow_origins=impostazioni.cors_origini,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(storico.router)
app.include_router(segnalazioni.router)


@app.get("/salute")
def salute():
    return {"ok": True}
