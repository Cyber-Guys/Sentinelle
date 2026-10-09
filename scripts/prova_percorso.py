"""Prova end-to-end contro il backend su localhost:8000."""
import httpx

API = "http://localhost:8000"
c = httpx.Client(base_url=API, timeout=60)


def punti(uid: int) -> int:
    return next(u["punti"] for u in c.get("/utenti").json() if u["id"] == uid)


p0 = punti(1)
print(f"1. punti utente 1 prima: {p0}")
s = c.post("/segnalazioni", data={"utente_id": 1, "tipo": "fuoco", "lat": 39.42, "lon": 8.92}).json()
print(f"2. creata segnalazione {s['id']}: priorita {s['priorita']}, stato {s['stato']}")
coda = c.get("/segnalazioni", params={"stato": "nuova"}).json()
trovata = next((x for x in coda if x["id"] == s["id"]), None)
assert trovata and trovata["motivazioni"], "segnalazione non in coda o senza motivazioni"
print(f"3. in coda (posizione {coda.index(trovata) + 1}/{len(coda)}), motivazioni:")
for m in trovata["motivazioni"]:
    print(f"   - {m}")
conf = c.post(f"/segnalazioni/{s['id']}/conferma").json()
assert conf["stato"] == "confermata"
print(f"4. confermata: stato {conf['stato']}")
p1 = punti(1)
assert p1 == p0 + 50, f"punti attesi {p0 + 50}, trovati {p1}"
print(f"5. punti utente 1 dopo: {p1} (+50) -> OK")
