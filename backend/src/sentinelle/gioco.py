"""Logica del gioco: livelli, quiz del giorno, preparazione tabelle e missioni."""
import random
import tomllib
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text

from .config import FILE_MISSIONI, FILE_QUIZ, FILE_SCHEMA

LIVELLI = [("Osservatore", 0), ("Sentinella", 100), ("Guardiano", 300), ("Custode del territorio", 700)]
DOMANDE_PER_QUIZ = 3
PUNTI_PER_RISPOSTA = 5
FUSO = ZoneInfo("Europe/Rome")


def oggi() -> date:
    """Giorno corrente in ora locale (limiti giornalieri e quiz)."""
    return datetime.now(FUSO).date()


def livello(punti: int) -> dict:
    i = max(k for k, (_, soglia) in enumerate(LIVELLI) if punti >= soglia)
    nome, soglia = LIVELLI[i]
    prossima = LIVELLI[i + 1][1] if i + 1 < len(LIVELLI) else None
    progresso = 1.0 if prossima is None else (punti - soglia) / (prossima - soglia)
    return {"nome": nome, "soglia": soglia, "prossima_soglia": prossima, "progresso": round(progresso, 3)}


def carica_domande() -> list[dict]:
    return tomllib.loads(FILE_QUIZ.read_text())["domanda"]


def quiz_del_giorno(giorno: date, domande: list[dict]) -> list[dict]:
    """3 domande scelte in modo deterministico dalla data (stesse per tutti, nello stesso giorno)."""
    scelte = random.Random(giorno.toordinal()).sample(range(len(domande)), DOMANDE_PER_QUIZ)
    return [domande[i] for i in scelte]


def correggi_quiz(giorno: date, risposte: list[int], domande: list[dict]) -> tuple[int, list[dict]]:
    quiz = quiz_del_giorno(giorno, domande)
    if len(risposte) != len(quiz):
        raise ValueError("numero di risposte errato")
    esiti = [{"indice": i, "giusta": r == q["corretta"], "corretta": q["corretta"], "spiegazione": q["spiegazione"]}
             for i, (q, r) in enumerate(zip(quiz, risposte))]
    return sum(e["giusta"] for e in esiti), esiti


def prepara_db(conn) -> None:
    """Crea le tabelle del gioco (IF NOT EXISTS) e fa l'upsert delle missioni per codice."""
    ddl = FILE_SCHEMA.read_text().split("-- gioco:", 1)[1]
    conn.execute(text(ddl.split("\n", 1)[1]))
    for m in tomllib.loads(FILE_MISSIONI.read_text())["missione"]:
        conn.execute(text(
            "INSERT INTO missione (codice, titolo, descrizione, punti, tipo) VALUES (:codice, :titolo, :descrizione, :punti, :tipo) "
            "ON CONFLICT (codice) DO UPDATE SET titolo = EXCLUDED.titolo, descrizione = EXCLUDED.descrizione, "
            "punti = EXCLUDED.punti, tipo = EXCLUDED.tipo"), m)
