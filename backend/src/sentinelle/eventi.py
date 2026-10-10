"""Eventi live: LISTEN/NOTIFY di Postgres inoltrati ai client via SSE."""
import asyncio
import json

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from .config import impostazioni
from .fonti.firms import hotspot_sardegna

router = APIRouter()
_code: set[asyncio.Queue] = set()
URL = impostazioni.database_url.replace("+psycopg", "")
INTERVALLO_HOTSPOT_S = 600


def _inoltra(payload: str) -> None:
    for q in _code:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


async def ascolta() -> None:
    attesa = 1
    while True:
        try:
            async with await psycopg.AsyncConnection.connect(URL, autocommit=True) as conn:
                await conn.execute("LISTEN sentinelle")
                attesa = 1
                async for n in conn.notifies():
                    _inoltra(n.payload)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(attesa)
            attesa = min(attesa * 2, 30)


def notifica_hotspot(n: int) -> None:
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("SELECT pg_notify('sentinelle', %s)", (json.dumps({"tipo": "hotspot_aggiornati", "n": n}),))


async def controlla_hotspot() -> None:
    firma = None
    primo = True
    while True:
        try:
            hs = await asyncio.to_thread(hotspot_sardegna)
            if hs is not None:
                nuova = (len(hs), max((h.rilevato_il for h in hs), default=None))
                if not primo and nuova != firma:
                    await asyncio.to_thread(notifica_hotspot, len(hs))
                firma, primo = nuova, False
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        await asyncio.sleep(INTERVALLO_HOTSPOT_S)


def _sse(payload: str) -> str:
    try:
        tipo = json.loads(payload)["tipo"]
    except Exception:
        return ""
    return f"event: {tipo}\ndata: {payload}\n\n"


@router.get("/eventi")
async def eventi(request: Request):
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _code.add(q)

    async def flusso():
        try:
            yield "event: pronto\ndata: {}\n\n"
            while not await request.is_disconnected():
                try:
                    yield _sse(await asyncio.wait_for(q.get(), 15))
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            _code.discard(q)

    return StreamingResponse(flusso(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
