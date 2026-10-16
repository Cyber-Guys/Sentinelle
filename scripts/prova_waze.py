"""Prova dello scenario 'Waze per gli incendi' contro il backend su localhost:8000."""
import httpx

c = httpx.Client(base_url="http://localhost:8000", timeout=60)
LAT, LON = 39.4353, 8.8961          # Serramanna
VICINO = {"lat": 39.44, "lon": 8.90}  # ~0,6 km
LONTANO = {"lat": 39.4433, "lon": 8.7346}  # Villacidro, ~14 km


def punti(uid: int) -> int:
    return c.get(f"/utenti/{uid}").json()["punti"]


p0 = {u: punti(u) for u in (1, 2, 3, 5)}
s = c.post("/segnalazioni", data={"utente_id": 1, "tipo": "fumo", "lat": LAT, "lon": LON}).json()
print(f"1. segnalazione fumo {s['id']} di Giulia (Serramanna), priorita {s['priorita']}, stato {s['stato_ufficiale']}")
d = c.get("/segnalazioni/vicine", params={"lat": 39.437, "lon": 8.897, "tipo": "fumo"}).json()
assert d and d["id"] == s["id"], d
print(f"2. doppione proposto: segnalazione {d['id']} a {d['distanza_m']} m, livello {d['affidabilita']['livello']}")
for u in (3, 5):
    v = c.post(f"/segnalazioni/{s['id']}/voto", data={"utente_id": u, "voto": "ancora", **VICINO})
    assert v.status_code == 200, v.text
    print(f"3. conferma utente {u}: valore {v.json()['affidabilita']['valore']}, livello {v.json()['affidabilita']['livello']}")
r = c.post(f"/segnalazioni/{s['id']}/voto", data={"utente_id": 508, "voto": "finito", **LONTANO})
assert r.status_code == 422, r.text
print(f"4. smentita da Villacidro rifiutata: {r.status_code} {r.json()['detail']}")
assert c.post(f"/segnalazioni/{s['id']}/voto", data={"utente_id": 3, "voto": "ancora", **VICINO}).status_code == 409
assert c.post(f"/segnalazioni/{s['id']}/voto", data={"utente_id": 1, "voto": "ancora", **VICINO}).status_code == 403
print("5. voto doppio 409, voto sulla propria 403")
att = c.get("/segnalazioni/attive", params={"utente_id": 3}).json()
a = next(x for x in att if x["id"] == s["id"])
assert a["conferme"] == 2 and a["mio_voto"] == "ancora" and "utente_id" not in a
conf = c.post(f"/segnalazioni/{s['id']}/conferma").json()
assert conf["stato"] == "confermata" and conf["stato_ufficiale"] == "allertati", conf
print(f"6. operatore conferma: stato ufficiale {conf['stato_ufficiale']}, priorita {conf['priorita']}")
assert punti(1) == p0[1] + 50 and punti(3) == p0[3] + 15 and punti(5) == p0[5] + 10
print("7. punti: Giulia +50, primo a confermare +15, secondo +10 -> OK")
assert c.post(f"/segnalazioni/{s['id']}/voto", data={"utente_id": 2, "voto": "finito", **VICINO}).status_code == 200
st = c.post(f"/segnalazioni/{s['id']}/stato", json={"stato_ufficiale": "spento"}).json()
assert st["stato_ufficiale"] == "spento" and punti(2) == p0[2] + 10
aff = c.get("/utenti/3").json()["affidabilita"]
print(f"8. spento: 'Non c'e' piu'' di Marco +10; affidabilita' utente 3 = {aff['valore']} ({aff['etichetta']}) -> OK")
