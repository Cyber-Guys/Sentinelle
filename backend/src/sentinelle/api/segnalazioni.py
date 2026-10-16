import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import DIR_FOTO
from ..db import engine
from ..fonti import meteo
from ..gioco import oggi
from ..rischio import rischio_meteo
from ..verifica import PESI, calcola_priorita, raccogli_contesto

router = APIRouter()

PUNTI_AREA = 10
PUNTI_AREA_LIMITE = 3

SELEZIONE = ("SELECT s.id, s.utente_id, s.tipo, ST_Y(s.geom) AS lat, ST_X(s.geom) AS lon, s.foto, s.priorita, "
             "s.motivazioni, s.fattori, s.stato, s.creata_il, s.valutata_il, s.punti_ottenuti, "
             "(SELECT c.nome FROM comune c WHERE ST_Intersects(c.geom, s.geom) LIMIT 1) AS comune "
             "FROM segnalazione s")


def _json(r) -> dict:
    return {"id": r.id, "utente_id": r.utente_id, "tipo": r.tipo, "lat": r.lat, "lon": r.lon,
            "foto_url": f"/foto/{r.foto}" if r.foto else None, "priorita": r.priorita,
            "motivazioni": r.motivazioni, "fattori": r.fattori or [], "comune": r.comune, "stato": r.stato, "creata_il": r.creata_il.isoformat(),
            "valutata_il": r.valutata_il.isoformat() if r.valutata_il else None, "punti_ottenuti": r.punti_ottenuti}


@router.post("/segnalazioni")
def crea_segnalazione(utente_id: int = Form(), tipo: str = Form(), lat: float = Form(), lon: float = Form(),
                      foto: UploadFile | None = File(None)):
    if tipo not in ("fuoco", "area_a_rischio"):
        raise HTTPException(422, "tipo non valido")
    nome_foto = None
    if foto and foto.filename:
        DIR_FOTO.mkdir(exist_ok=True)
        nome_foto = uuid.uuid4().hex + Path(foto.filename).suffix.lower()
        (DIR_FOTO / nome_foto).write_bytes(foto.file.read())
    with Session(engine) as s:
        esito = calcola_priorita(raccogli_contesto(s, lat, lon), PESI)
        nuovo = s.execute(text(
            "INSERT INTO segnalazione (utente_id, tipo, geom, foto, priorita, motivazioni, fattori) "
            "VALUES (:u, :t, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :f, :p, CAST(:m AS jsonb), "
            "CAST(:fa AS jsonb)) RETURNING id"),
            {"u": utente_id, "t": tipo, "lon": lon, "lat": lat, "f": nome_foto, "p": esito.priorita,
             "m": json.dumps(esito.motivazioni), "fa": json.dumps(esito.fattori)}).scalar()
        punti_ottenuti = 0
        if tipo == "area_a_rischio":
            # +10 subito, al massimo 3 segnalazioni al giorno (ora locale) che danno punti
            oggi_n = s.execute(text(
                "SELECT count(*) FROM segnalazione WHERE utente_id = :u AND tipo = 'area_a_rischio' "
                "AND (creata_il AT TIME ZONE 'Europe/Rome')::date = :g"), {"u": utente_id, "g": oggi()}).scalar()
            if oggi_n <= PUNTI_AREA_LIMITE:  # include quella appena inserita
                punti_ottenuti = PUNTI_AREA
                s.execute(text("UPDATE utente SET punti = punti + :p WHERE id = :u"),
                          {"p": punti_ottenuti, "u": utente_id})
                s.execute(text("UPDATE segnalazione SET punti_ottenuti = :p WHERE id = :i"),
                          {"p": punti_ottenuti, "i": nuovo})
        s.commit()
        return _json(s.execute(text(SELEZIONE + " WHERE s.id = :i"), {"i": nuovo}).one())


@router.get("/segnalazioni")
def elenco(stato: str = "nuova", utente_id: int | None = None, limite: int = 500):
    cond, par = [], {"l": limite}
    if stato == "valutate":
        cond.append("s.stato IN ('confermata', 'archiviata')")
    elif stato != "tutte":
        cond.append("s.stato = :s")
        par["s"] = stato
    if utente_id is not None:
        cond.append("s.utente_id = :u")
        par["u"] = utente_id
    ordine = "s.priorita DESC, s.creata_il DESC" if stato == "nuova" else "COALESCE(s.valutata_il, s.creata_il) DESC"
    with engine.connect() as c:
        righe = c.execute(text(SELEZIONE + (" WHERE " + " AND ".join(cond) if cond else "")
                               + f" ORDER BY {ordine} LIMIT :l"), par).all()
    return [_json(r) for r in righe]


def _cambia_stato(id: int, nuovo: str) -> dict:
    with Session(engine) as s:
        r = s.execute(text("UPDATE segnalazione SET stato = :n, valutata_il = now() WHERE id = :i RETURNING tipo, utente_id"),
                      {"n": nuovo, "i": id}).one_or_none()
        if r is None:
            raise HTTPException(404, "segnalazione non trovata")
        if nuovo == "confermata" and r.tipo == "fuoco":
            s.execute(text("UPDATE utente SET punti = punti + 50 WHERE id = :u"), {"u": r.utente_id})
            s.execute(text("UPDATE segnalazione SET punti_ottenuti = 50 WHERE id = :i"), {"i": id})
        s.commit()
        return _json(s.execute(text(SELEZIONE + " WHERE s.id = :i"), {"i": id}).one())


@router.post("/segnalazioni/{id}/conferma")
def conferma(id: int):
    return _cambia_stato(id, "confermata")


@router.post("/segnalazioni/{id}/archivia")
def archivia(id: int):
    return _cambia_stato(id, "archiviata")


@router.get("/rischio")
def rischio(lat: float, lon: float):
    m = meteo(lat, lon)
    if m is None:
        return {"valore": 0.0, "livello": "basso", "meteo": None}
    v = rischio_meteo(m)
    return {"valore": v, "livello": "basso" if v < 0.33 else "medio" if v < 0.66 else "alto", "meteo": vars(m)}


@router.get("/rischio/comune")
def rischio_comune(nome: str, lat: float, lon: float):
    """Indicatore dell'app: stesso indice per cella delle aree critiche, meteo del punto per il dettaglio."""
    from ..aree_critiche import indice_comune, livello_indice
    v = round(indice_comune(nome, lat, lon), 3)
    m = meteo(lat, lon)
    return {"valore": v, "livello": livello_indice(v), "meteo": vars(m) if m else None}


@router.get("/foto/{nome}")
def foto(nome: str):
    percorso = DIR_FOTO / Path(nome).name
    if not percorso.is_file():
        raise HTTPException(404)
    return FileResponse(percorso)
