import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import DIR_FOTO
from ..db import engine
from .. import missioni_mirate
from ..gioco import PUNTI_PER_RISPOSTA, carica_domande, correggi_quiz, livello, oggi, quiz_del_giorno

router = APIRouter()

LIMITI_GIORNALIERI = {"quiz": 1, "posizione": 3}  # per missione
DOMANDE = carica_domande()
GIORNO_LOCALE = "(completata_il AT TIME ZONE 'Europe/Rome')::date"


def _utente(s: Session, utente_id: int):
    r = s.execute(text("SELECT u.id, u.nome, c.nome AS comune, u.punti FROM utente u "
                       "LEFT JOIN comune c ON c.id = u.comune_id WHERE u.id = :i"), {"i": utente_id}).one_or_none()
    if r is None:
        raise HTTPException(404, "utente non trovato")
    return r


def _conteggi(s: Session, utente_id: int, missione_id: int) -> tuple[int, int]:
    """(completamenti oggi, completamenti totali) dell'utente per la missione."""
    r = s.execute(text(f"SELECT count(*) FILTER (WHERE {GIORNO_LOCALE} = :g), count(*) FROM missione_completata "
                       "mc WHERE utente_id = :u AND missione_id = :m "
                       "AND NOT EXISTS (SELECT 1 FROM missione_mirata mm WHERE mm.completamento_id = mc.id)"),
                  {"g": oggi(), "u": utente_id, "m": missione_id}).one()
    return r[0], r[1]


def _limite(tipo: str, oggi_n: int, totale: int) -> str | None:
    """Motivo per cui la missione non e' disponibile, None se lo e'."""
    if tipo == "esplora":
        return "Già completata" if totale >= 1 else None
    massimo = LIMITI_GIORNALIERI[tipo]
    if oggi_n >= massimo:
        return "Già fatta oggi" if massimo == 1 else f"Limite di {massimo} al giorno raggiunto"
    return None


@router.get("/utenti/{id}")
def utente(id: int):
    with Session(engine) as s:
        u = _utente(s, id)
    return {"id": u.id, "nome": u.nome, "comune": u.comune, "punti": u.punti, "livello": livello(u.punti)}


@router.get("/missioni")
def missioni(utente_id: int):
    with Session(engine) as s:
        _utente(s, utente_id)
        out = []
        for m in s.execute(text("SELECT id, codice, titolo, descrizione, punti, tipo FROM missione ORDER BY id")).all():
            motivo = _limite(m.tipo, *_conteggi(s, utente_id, m.id))
            out.append({"id": m.id, "codice": m.codice, "titolo": m.titolo, "descrizione": m.descrizione,
                        "punti": m.punti, "tipo": m.tipo, "disponibile": motivo is None, "motivo": motivo})
    return out


@router.get("/quiz/oggi")
def quiz_oggi():
    return [{"indice": i, "domanda": q["domanda"], "opzioni": q["opzioni"]}
            for i, q in enumerate(quiz_del_giorno(oggi(), DOMANDE))]


def _salva_foto(foto: UploadFile | None) -> str | None:
    if not (foto and foto.filename):
        return None
    DIR_FOTO.mkdir(exist_ok=True)
    nome = uuid.uuid4().hex + Path(foto.filename).suffix.lower()
    (DIR_FOTO / nome).write_bytes(foto.file.read())
    return nome


@router.get("/missioni/mirate")
def mirate(utente_id: int):
    with engine.begin() as c:
        with Session(bind=c) as s:
            _utente(s, utente_id)
        return missioni_mirate.di_oggi(c, utente_id)


# esito del sopralluogo -> tipo di mappatura creata (area pulita: sopralluogo vegetazione con esito negativo)
ESITI_MIRATA = {"pulita": "sterpaglie", "sterpaglie": "sterpaglie", "rifiuti": "rifiuti_strada"}


@router.post("/missioni/mirate/{id}/completa")
def completa_mirata(id: int, lat: float = Form(), lon: float = Form(), esito: str = Form(),
                    foto: UploadFile | None = File(None)):
    if esito not in ESITI_MIRATA:
        raise HTTPException(422, "Scegli cosa hai trovato: area pulita, sterpaglie secche o rifiuti infiammabili")
    with Session(engine) as s:
        m = s.execute(text(
            "SELECT id, utente_id, punti, completata_il, scade_il < now() AS scaduta, ST_Distance(geom::geography, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS dist FROM missione_mirata WHERE id = :i FOR UPDATE"),
            {"i": id, "lon": lon, "lat": lat}).one_or_none()
        if m is None:
            raise HTTPException(404, "missione non trovata")
        if m.completata_il is not None:
            raise HTTPException(409, "Già completata")
        if m.scaduta:
            raise HTTPException(409, "Missione scaduta")
        if m.dist > missioni_mirate.RAGGIO_COMPLETAMENTO_M:
            raise HTTPException(422, f"Sei a {m.dist / 1000:.1f} km dal punto: avvicinati entro 1 km")
        mc = s.execute(text(
            "INSERT INTO missione_completata (utente_id, missione_id, punti, geom, foto, esito) SELECT :u, id, :p, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :f, :e FROM missione WHERE codice = :k RETURNING id"),
            {"u": m.utente_id, "p": m.punti, "lon": lon, "lat": lat, "f": _salva_foto(foto), "e": esito,
             "k": ESITI_MIRATA[esito]}).scalar()
        s.execute(text("UPDATE missione_mirata SET completata_il = now(), completamento_id = :c, esito = :e WHERE id = :i"),
                  {"c": mc, "i": id, "e": esito})
        totale = s.execute(text("UPDATE utente SET punti = punti + :p WHERE id = :u RETURNING punti"),
                           {"p": m.punti, "u": m.utente_id}).scalar()
        s.commit()
    return {"punti_ottenuti": m.punti, "punti": totale, "livello": livello(totale)}


@router.post("/missioni/{id}/completa")
def completa(id: int, utente_id: int = Form(), lat: float | None = Form(None), lon: float | None = Form(None),
             foto: UploadFile | None = File(None), risposte: str | None = Form(None)):
    with Session(engine) as s:
        _utente(s, utente_id)
        m = s.execute(text("SELECT id, punti, tipo FROM missione WHERE id = :i"), {"i": id}).one_or_none()
        if m is None:
            raise HTTPException(404, "missione non trovata")
        motivo = _limite(m.tipo, *_conteggi(s, utente_id, id))
        if motivo:
            raise HTTPException(409, motivo)

        punti, esiti, geom, nome_foto = m.punti, None, None, None
        if m.tipo == "quiz":
            try:
                giuste, esiti = correggi_quiz(oggi(), [int(r) for r in json.loads(risposte or "")], DOMANDE)
            except (ValueError, TypeError):
                raise HTTPException(422, "risposte non valide: serve una lista di interi, una per domanda")
            punti = giuste * PUNTI_PER_RISPOSTA
        elif m.tipo == "posizione":
            if lat is None or lon is None:
                raise HTTPException(422, "lat e lon obbligatori")
            geom = (lon, lat)
            nome_foto = _salva_foto(foto)

        s.execute(text(
            "INSERT INTO missione_completata (utente_id, missione_id, punti, geom, foto) VALUES "
            "(:u, :m, :p, CASE WHEN CAST(:lon AS float) IS NULL THEN NULL ELSE ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) END, :f)"),
            {"u": utente_id, "m": id, "p": punti, "lon": geom[0] if geom else None, "lat": geom[1] if geom else None,
             "f": nome_foto})
        totale = s.execute(text("UPDATE utente SET punti = punti + :p WHERE id = :u RETURNING punti"),
                           {"p": punti, "u": utente_id}).scalar()
        s.commit()
    risposta = {"punti_ottenuti": punti, "punti": totale, "livello": livello(totale)}
    if esiti is not None:
        risposta["esiti"] = esiti
    return risposta


@router.get("/classifica/comuni")
def classifica_comuni():
    with engine.connect() as c:
        righe = c.execute(text(
            "SELECT co.nome AS comune, sum(u.punti) AS punti, count(*) FILTER (WHERE u.punti > 0) AS utenti "
            "FROM utente u JOIN comune co ON co.id = u.comune_id GROUP BY co.nome "
            "HAVING sum(u.punti) > 0 ORDER BY punti DESC, co.nome LIMIT 20")).all()
    return [{"comune": r.comune, "punti": int(r.punti), "utenti": r.utenti} for r in righe]


@router.get("/classifica/utenti")
def classifica_utenti(comune_id: int):
    with engine.connect() as c:
        righe = c.execute(text("SELECT nome, punti FROM utente WHERE comune_id = :c ORDER BY punti DESC, nome LIMIT 20"),
                          {"c": comune_id}).all()
    return [{"nome": r.nome, "punti": r.punti, "livello": livello(r.punti)["nome"]} for r in righe]


@router.get("/mappature")
def mappature():
    with engine.connect() as c:
        righe = c.execute(text(
            "SELECT m.codice, m.titolo, u.nome AS utente, mc.completata_il, mc.esito, ST_AsGeoJSON(mc.geom) AS g, "
            "EXISTS (SELECT 1 FROM missione_mirata mm WHERE mm.completamento_id = mc.id) AS mirata "
            "FROM missione_completata mc JOIN missione m ON m.id = mc.missione_id "
            "JOIN utente u ON u.id = mc.utente_id WHERE m.tipo = 'posizione' AND mc.geom IS NOT NULL "
            "ORDER BY mc.completata_il DESC LIMIT 2000")).all()
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": json.loads(r.g), "properties": {
            "codice": r.codice, "titolo": r.titolo, "utente": r.utente, "completata_il": r.completata_il.isoformat(), "mirata": r.mirata,
            "esito": r.esito}}
        for r in righe]}
