"""Prova del gioco via HTTP (BASE_URL, default http://localhost:8000). Lascia punti sull'utente 1: rieseguire dopo reset_demo.sql."""
import json
import os

import httpx

c = httpx.Client(base_url=os.environ.get("BASE_URL", "http://localhost:8000"), timeout=60)
UID = 1


def utente() -> dict:
    return c.get(f"/utenti/{UID}").json()


u0 = utente()
print(f"1. utente {UID}: {u0['punti']} punti, livello {u0['livello']['nome']}")
if u0["punti"]:
    print("   (nota: l'utente ha gia' punti; i limiti giornalieri potrebbero dare 409: eseguire reset_demo.sql)")

quiz = c.get("/quiz/oggi").json()
assert len(quiz) == 3 and all("corretta" not in q and "soluzione" not in q for q in quiz), "il quiz non deve rivelare la soluzione"
print(f"2. quiz di oggi: {len(quiz)} domande, nessuna soluzione nel payload")
miss = {m["codice"]: m for m in c.get("/missioni", params={"utente_id": UID}).json()}
assert miss["quiz_rischio"]["disponibile"], "quiz gia' fatto oggi: eseguire reset_demo.sql"

# Si risponde 0 a tutto: il punteggio dipende da quante coincidono, e gli esiti rivelano le soluzioni.
r = c.post(f"/missioni/{miss['quiz_rischio']['id']}/completa", data={"utente_id": UID, "risposte": json.dumps([0, 0, 0])})
assert r.status_code == 200, r.text
q = r.json()
giuste = sum(e["giusta"] for e in q["esiti"])
assert q["punti_ottenuti"] == 5 * giuste
print(f"3. quiz consegnato: {giuste}/3 giuste, +{q['punti_ottenuti']} punti, totale {q['punti']}, livello {q['livello']['nome']}")

r2 = c.post(f"/missioni/{miss['quiz_rischio']['id']}/completa", data={"utente_id": UID, "risposte": json.dumps([0, 0, 0])})
assert r2.status_code == 409, r2.status_code
print(f"4. secondo quiz nello stesso giorno: {r2.status_code} {r2.json()['detail']} -> OK")

# punteggio pieno: si verifica con un secondo utente sulla correttezza del calcolo usando le soluzioni restituite
altro = 2
sol = [e["corretta"] for e in q["esiti"]]
b0 = c.get(f"/utenti/{altro}").json()["punti"]
r3 = c.post(f"/missioni/{miss['quiz_rischio']['id']}/completa", data={"utente_id": altro, "risposte": json.dumps(sol)})
assert r3.status_code == 200 and r3.json()["punti_ottenuti"] == 15, r3.text
assert c.get(f"/utenti/{altro}").json()["punti"] == b0 + 15
print(f"5. utente {altro} con tutte le risposte giuste: +15 punti -> OK")

p = c.post(f"/missioni/{miss['sterpaglie']['id']}/completa", data={"utente_id": UID, "lat": 39.42, "lon": 8.92})
assert p.status_code == 200 and p.json()["punti_ottenuti"] == 20, p.text
print(f"6. missione posizione 'sterpaglie': +{p.json()['punti_ottenuti']} punti, totale {p.json()['punti']}")

e = c.post(f"/missioni/{miss['esplora_comune']['id']}/completa", data={"utente_id": UID})
if e.status_code == 200:
    print(f"7. missione esplora: +{e.json()['punti_ottenuti']} punti")
    assert c.post(f"/missioni/{miss['esplora_comune']['id']}/completa", data={"utente_id": UID}).status_code == 409
    print("   seconda volta: 409 -> OK")
else:
    print(f"7. missione esplora gia' fatta: {e.status_code}")

before = utente()["punti"]
s = c.post("/segnalazioni", data={"utente_id": UID, "tipo": "area_a_rischio", "lat": 39.42, "lon": 8.92}).json()
assert s["punti_ottenuti"] == 10 and utente()["punti"] == before + 10
print(f"8. area_a_rischio: +{s['punti_ottenuti']} punti -> OK")

cl = c.get("/classifica/comuni").json()
assert cl, "classifica comuni vuota"
print("9. classifica comuni:", [(x["comune"], x["punti"], x["utenti"]) for x in cl[:5]])
assert c.get("/mappature").json()["features"], "nessuna mappatura"
print("10. mappature presenti -> OK")
print("TUTTO OK")
