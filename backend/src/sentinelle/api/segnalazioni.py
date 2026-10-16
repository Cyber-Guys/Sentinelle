import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import DIR_FOTO
from ..db import engine
from ..fonti import meteo
from ..gioco import oggi
from ..rischio import rischio_meteo
from ..affidabilita import CONF, FUOCO, Prove, Voto, affidabilita_utente, probabilmente_spento, punteggio
from ..verifica import PESI, calcola_priorita, con_affidabilita, raccogli_contesto

router = APIRouter()

PUNTI_AREA = 10
PUNTI_AREA_LIMITE = 3
TIPI = ("fuoco", "fumo", "area_a_rischio")
STATI_UFFICIALI = ("in_verifica", "allertati", "mezzi_sul_posto", "spento")
PUNTI_VOTO, PUNTI_PRIMO = 10, 5
LIVELLI = {"da_verificare": "Da verificare", "probabile": "Probabile",
           "comunita": "Confermata dalla comunità", "operatori": "Confermata dagli operatori"}

SELEZIONE = ("SELECT s.id, s.utente_id, s.tipo, ST_Y(s.geom) AS lat, ST_X(s.geom) AS lon, s.foto, s.priorita, "
             "s.motivazioni, s.fattori, s.stato, s.creata_il, s.valutata_il, s.punti_ottenuti, s.stato_ufficiale, s.aggiornata_il, "
             "(SELECT count(*) FROM voto_segnalazione v WHERE v.segnalazione_id = s.id AND v.voto = 'ancora') AS conferme, "
             "(SELECT count(*) FROM voto_segnalazione v WHERE v.segnalazione_id = s.id AND v.voto = 'finito') AS smentite, "
             "(SELECT c.nome FROM comune c WHERE ST_Intersects(c.geom, s.geom) LIMIT 1) AS comune "
             "FROM segnalazione s")


def _json(r) -> dict:
    return {"id": r.id, "utente_id": r.utente_id, "tipo": r.tipo, "lat": r.lat, "lon": r.lon,
            "foto_url": f"/foto/{r.foto}" if r.foto else None, "priorita": r.priorita,
            "motivazioni": r.motivazioni, "fattori": r.fattori or [], "comune": r.comune, "stato": r.stato, "creata_il": r.creata_il.isoformat(),
            "valutata_il": r.valutata_il.isoformat() if r.valutata_il else None, "punti_ottenuti": r.punti_ottenuti,
            "stato_ufficiale": r.stato_ufficiale, "aggiornata_il": r.aggiornata_il.isoformat(),
            "conferme": r.conferme, "smentite": r.smentite}


def affidabilita_utenti(s, ids) -> dict[int, float]:
    """r = (esiti giusti + 1) / (esiti valutati + 2) su segnalazioni proprie e voti, dagli esiti operatore."""
    ids = list({i for i in ids if i is not None})
    if not ids:
        return {}
    righe = s.execute(text(
        "SELECT u, sum(ok) AS ok, sum(val) AS val FROM ("
        " SELECT utente_id AS u, (stato = 'confermata')::int AS ok, 1 AS val FROM segnalazione"
        "  WHERE stato IN ('confermata', 'archiviata') AND utente_id = ANY(:ids)"
        " UNION ALL SELECT v.utente_id, CASE WHEN v.voto = 'ancora' THEN (x.stato = 'confermata')::int"
        "  ELSE (x.stato = 'archiviata' OR x.stato_ufficiale = 'spento')::int END,"
        "  CASE WHEN v.voto = 'ancora' THEN (x.stato IN ('confermata', 'archiviata'))::int"
        "  ELSE (x.stato IN ('confermata', 'archiviata') OR x.stato_ufficiale = 'spento')::int END"
        "  FROM voto_segnalazione v JOIN segnalazione x ON x.id = v.segnalazione_id WHERE v.utente_id = ANY(:ids)"
        ") t GROUP BY u"), {"ids": ids}).all()
    out = {i: affidabilita_utente(0, 0) for i in ids}
    out.update({r.u: affidabilita_utente(r.ok, r.val) for r in righe})
    return out


def _valore(fattori, chiave) -> float:
    return next((f.get("valore", 0) for f in fattori or [] if f.get("chiave") == chiave), 0)


def _valuta(r, voti, aff) -> tuple:
    """(Punteggio, probabilmente_spento) di una riga di segnalazione; voti = righe (utente_id, voto, eta_min)."""
    lista = [Voto("ancora", aff.get(r.utente_id, 0.5), r.eta_min)] + \
            [Voto(v.voto, aff.get(v.utente_id, 0.5), v.eta_min) for v in voti]
    prove = Prove(hotspot=_valore(r.fattori, "hotspot") >= 0.8, foto=bool(r.foto),
                  rischio_alto=_valore(r.fattori, "pericolo") >= 0.75, operatore=r.stato == "confermata")
    return punteggio(lista, prove, r.eta_min, r.tipo), probabilmente_spento(lista)


CONDIVISA = ("SELECT s.id, s.utente_id, s.tipo, ST_Y(s.geom) AS lat, ST_X(s.geom) AS lon, s.foto, s.fattori, s.stato, "
             "s.stato_ufficiale, s.creata_il, s.aggiornata_il, (extract(epoch FROM now() - s.creata_il) / 60)::float AS eta_min "
             "FROM segnalazione s")


def condivise(s, cond: str, par: dict, utente_id: int | None) -> list[dict]:
    righe = s.execute(text(CONDIVISA + " WHERE " + cond + " ORDER BY s.creata_il DESC"), par).all()
    if not righe:
        return []
    voti = s.execute(text("SELECT segnalazione_id, utente_id, voto, (extract(epoch FROM now() - creato_il) / 60)::float AS eta_min "
                          "FROM voto_segnalazione WHERE segnalazione_id = ANY(:ids)"), {"ids": [r.id for r in righe]}).all()
    aff = affidabilita_utenti(s, [r.utente_id for r in righe] + [v.utente_id for v in voti])
    out = []
    for r in righe:
        vr = [v for v in voti if v.segnalazione_id == r.id]
        p, spento = _valuta(r, vr, aff)
        out.append({"id": r.id, "tipo": r.tipo, "lat": r.lat, "lon": r.lon, "creata_il": r.creata_il.isoformat(),
                    "aggiornata_il": r.aggiornata_il.isoformat(), "stato_ufficiale": r.stato_ufficiale,
                    "affidabilita": {"valore": p.valore, "livello": p.livello, "etichetta": LIVELLI[p.livello],
                                     "fattori": p.fattori},
                    "conferme": sum(v.voto == "ancora" for v in vr), "smentite": sum(v.voto == "finito" for v in vr),
                    "probabilmente_spento": spento and r.stato_ufficiale != "spento",
                    "foto_url": f"/foto/{r.foto}" if r.foto else None, "mia": r.utente_id == utente_id,
                    "mio_voto": next((v.voto for v in vr if v.utente_id == utente_id), None)})
    return out


def aggiorna_priorita(s, id: int) -> None:
    """Ricalcola il fattore additivo 'affidabilita' della priorita' e tocca aggiornata_il (-> evento SSE)."""
    c = condivise(s, "s.id = :i", {"i": id}, None)[0]
    a = c["affidabilita"]
    fattori = s.execute(text("SELECT fattori FROM segnalazione WHERE id = :i"), {"i": id}).scalar()
    testo = f"{LIVELLI[a['livello']]} · {c['conferme']} conferme, {c['smentite']} smentite"
    pr, fa = con_affidabilita(fattori, 99 if a["livello"] == "operatori" else a["valore"], testo,
                              CONF["peso_priorita"], CONF["soglia_comunita"])
    s.execute(text("UPDATE segnalazione SET priorita = :p, fattori = CAST(:f AS jsonb), aggiornata_il = now() "
                   "WHERE id = :i"), {"p": pr, "f": json.dumps(fa), "i": id})


@router.post("/segnalazioni")
def crea_segnalazione(utente_id: int = Form(), tipo: str = Form(), lat: float = Form(), lon: float = Form(),
                      foto: UploadFile | None = File(None)):
    if tipo not in TIPI:
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
        aggiorna_priorita(s, nuovo)
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


def _punti(s, utente_id: int, p: int) -> None:
    s.execute(text("UPDATE utente SET punti = punti + :p WHERE id = :u"), {"p": p, "u": utente_id})


def _cambia_stato(id: int, nuovo: str) -> dict:
    with Session(engine) as s:
        prima = s.execute(text("SELECT stato FROM segnalazione WHERE id = :i FOR UPDATE"), {"i": id}).scalar()
        if prima is None:
            raise HTTPException(404, "segnalazione non trovata")
        r = s.execute(text(
            "UPDATE segnalazione SET stato = :n, valutata_il = now(), stato_ufficiale = CASE WHEN :n = 'confermata' "
            "AND stato_ufficiale = 'in_verifica' THEN 'allertati' ELSE stato_ufficiale END "
            "WHERE id = :i RETURNING tipo, utente_id"), {"n": nuovo, "i": id}).one()
        if nuovo == "confermata" and prima != "confermata":
            # punti all'esito: autore +50 fuoco/fumo, +20 altri; chi ha votato "ancora" +10, il primo +5
            pa = 50 if r.tipo in FUOCO else 20
            _punti(s, r.utente_id, pa)
            s.execute(text("UPDATE segnalazione SET punti_ottenuti = punti_ottenuti + :p WHERE id = :i"), {"p": pa, "i": id})
            ancora = s.execute(text("SELECT utente_id FROM voto_segnalazione WHERE segnalazione_id = :i AND voto = 'ancora' "
                                    "ORDER BY creato_il, id"), {"i": id}).scalars().all()
            for k, u in enumerate(ancora):
                _punti(s, u, PUNTI_VOTO + (PUNTI_PRIMO if k == 0 else 0))
        aggiorna_priorita(s, id)
        s.commit()
        return _json(s.execute(text(SELEZIONE + " WHERE s.id = :i"), {"i": id}).one())


@router.post("/segnalazioni/{id}/conferma")
def conferma(id: int):
    return _cambia_stato(id, "confermata")


@router.post("/segnalazioni/{id}/archivia")
def archivia(id: int):
    return _cambia_stato(id, "archiviata")


def _filtro_attive() -> str:
    return ("s.stato <> 'archiviata' AND NOT (s.stato_ufficiale = 'spento' AND s.aggiornata_il < now() - interval '1 hour')")


@router.get("/segnalazioni/attive")
def attive(bbox: str | None = None, utente_id: int | None = None):
    """Tutte le segnalazioni attive (senza nomi); bbox = ovest,sud,est,nord."""
    cond, par = _filtro_attive(), {}
    if bbox:
        o, su, e, n = (float(x) for x in bbox.split(","))
        cond += " AND s.geom && ST_MakeEnvelope(:o, :su, :e, :n, 4326)"
        par.update(o=o, su=su, e=e, n=n)
    with Session(engine) as s:
        return condivise(s, cond, par, utente_id)


@router.get("/segnalazioni/vicine")
def vicine(lat: float, lon: float, tipo: str, utente_id: int | None = None):
    """Possibile doppione: stessa tipologia entro il raggio e la finestra di tempo, la piu' vicina; altrimenti null."""
    raggio = CONF["raggio_doppione_fuoco_m"] if tipo in FUOCO else CONF["raggio_doppione_altri_m"]
    punto = "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography"
    with Session(engine) as s:
        id = s.execute(text(
            f"SELECT s.id FROM segnalazione s WHERE {_filtro_attive()} AND s.stato_ufficiale <> 'spento' AND s.tipo = :t "
            f"AND s.creata_il > now() - make_interval(mins => :f) AND ST_DWithin(s.geom::geography, {punto}, :r) "
            f"ORDER BY ST_Distance(s.geom::geography, {punto}) LIMIT 1"),
            {"lat": lat, "lon": lon, "t": tipo, "r": raggio, "f": CONF["finestra_doppione_min"]}).scalar()
        if id is None:
            return None
        c = condivise(s, "s.id = :i", {"i": id}, utente_id)[0]
        c["distanza_m"] = round(s.execute(text(f"SELECT ST_Distance(geom::geography, {punto}) FROM segnalazione "
                                               "WHERE id = :i"), {"lat": lat, "lon": lon, "i": id}).scalar())
        return c


@router.post("/segnalazioni/{id}/voto")
def vota(id: int, utente_id: int = Form(), voto: str = Form(), lat: float = Form(), lon: float = Form()):
    if voto not in ("ancora", "finito"):
        raise HTTPException(422, "voto non valido")
    with Session(engine) as s:
        r = s.execute(text("SELECT utente_id, ST_Distance(geom::geography, "
                           "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS d FROM segnalazione WHERE id = :i"),
                      {"i": id, "lat": lat, "lon": lon}).one_or_none()
        if r is None:
            raise HTTPException(404, "segnalazione non trovata")
        if r.utente_id == utente_id:
            raise HTTPException(403, "non puoi votare la tua segnalazione")
        if r.d > CONF["raggio_conferma_m"]:
            raise HTTPException(422, f"Avvicinati entro {CONF['raggio_conferma_m'] // 1000} km per confermare")
        ok = s.execute(text("INSERT INTO voto_segnalazione (segnalazione_id, utente_id, voto, geom) "
                            "VALUES (:i, :u, :v, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) "
                            "ON CONFLICT (segnalazione_id, utente_id) DO NOTHING RETURNING id"),
                       {"i": id, "u": utente_id, "v": voto, "lat": lat, "lon": lon}).scalar()
        if ok is None:
            raise HTTPException(409, "voto gia' dato")
        aggiorna_priorita(s, id)
        s.commit()
        return condivise(s, "s.id = :i", {"i": id}, utente_id)[0]


class StatoUfficiale(BaseModel):
    stato_ufficiale: str


@router.post("/segnalazioni/{id}/stato")
def imposta_stato(id: int, corpo: StatoUfficiale):
    if corpo.stato_ufficiale not in STATI_UFFICIALI:
        raise HTTPException(422, "stato ufficiale non valido")
    with Session(engine) as s:
        prima = s.execute(text("SELECT stato_ufficiale FROM segnalazione WHERE id = :i FOR UPDATE"), {"i": id}).scalar()
        if prima is None:
            raise HTTPException(404, "segnalazione non trovata")
        s.execute(text("UPDATE segnalazione SET stato_ufficiale = :n, aggiornata_il = now() WHERE id = :i"),
                  {"n": corpo.stato_ufficiale, "i": id})
        if corpo.stato_ufficiale == "spento" and prima != "spento":
            # chiusura come spento: +10 a chi aveva detto "Non c'e' piu'"
            for u in s.execute(text("SELECT utente_id FROM voto_segnalazione WHERE segnalazione_id = :i "
                                    "AND voto = 'finito'"), {"i": id}).scalars():
                _punti(s, u, PUNTI_VOTO)
        s.commit()
        return _json(s.execute(text(SELEZIONE + " WHERE s.id = :i"), {"i": id}).one())


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
