"""Prova end-to-end del backend per la webapp cittadino (piano 2026-10-16-webapp-cittadino).
Backend attivo. Nel container: ./scripts/docker.sh exec -T backend python scripts/prova_webapp.py
Crea l'utente "Prova webapp (demo)" (lo cancella semina_demo.py) e archivia la segnalazione di prova."""
import base64
import os

import httpx

c = httpx.Client(base_url=os.environ.get("BASE_URL", "http://localhost:8000"), timeout=60)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
SERRAMANNA, SAMASSI = (39.4423, 8.9024), (39.4936, 8.9071)


def ok(r: httpx.Response, atteso: int = 200) -> dict:
    assert r.status_code == atteso, f"{r.request.method} {r.request.url.path}: {r.status_code} {r.text[:200]}"
    return r.json() if r.content else {}


u = ok(c.post("/utenti", json={"nome": "Prova webapp (demo)", "telefono": "+39 340 000 0000"}), 201)
uid = u["id"]
print("1. utente", uid, u["nome"], u["telefono"])

casa = ok(c.post(f"/utenti/{uid}/localita", json={"nome": "Casa", "tipo": "casa", "lat": SERRAMANNA[0], "lon": SERRAMANNA[1],
                                                  "indirizzo": "Via Roma 12, Serramanna"}), 201)
terreno = ok(c.post(f"/utenti/{uid}/localita", json={"nome": "Terreno", "tipo": "terreno", "lat": SAMASSI[0], "lon": SAMASSI[1],
                                                     "raggio_km": 10, "urgenza": "tutti",
                                                     "avvisi_tipi": ["fuoco", "fumo", "area_a_rischio"]}), 201)
elenco = ok(c.get(f"/utenti/{uid}/localita"))
assert [l["nome"] for l in elenco] == ["Casa", "Terreno"]
print("2. localita", [(l["nome"], l["stato"]["livello"], l["stato"]["n_zone"]) for l in elenco])
assert ok(c.get(f"/utenti/{uid}")).get("comune"), "la prima casa deve assegnare il comune"

r = ok(c.post("/segnalazioni", data={"utente_id": uid, "tipo": "fuoco", "lat": 39.4500, "lon": 8.9100, "nota": "Dietro la chiesa",
                                     "direzione": 405},
              files={"foto": ("f.png", PNG, "image/png"), "video": ("v.mp4", b"\x00\x00\x00\x18ftypmp42" + b"0" * 2000, "video/mp4")}))
assert r["foto_url"] and r["video_url"] and r["nota"] == "Dietro la chiesa" and r["direzione"] == 45, r
print("3. segnalazione", r["id"], "priorita", r["priorita"], r["foto_url"], r["video_url"])

avvisi = ok(c.get(f"/utenti/{uid}/avvisi"))
assert any(a["priorita"] == "urgente" and a["tipo"] == "fuoco" and a["localita_nome"] == "Casa" for a in avvisi), avvisi
print("4. avvisi", [(a["priorita"], a["titolo"]) for a in avvisi])

storico = ok(c.get(f"/utenti/{uid}/storico"))
s0 = storico["segnalazioni"][0]
assert storico["casa_nome"] == "Casa" and s0["id"] == r["id"] and s0["km_casa"] is not None and s0["comune"], storico
print("5. storico", s0["comune"], s0["km_casa"], "km da", storico["casa_nome"])

assert len(c.get(r["video_url"]).content) > 1000 and c.get(r["foto_url"]).status_code == 200
print("6. media letti da", r["video_url"])

coda = ok(c.get("/segnalazioni", params={"stato": "nuova"}))
mia = next(s for s in coda if s["id"] == r["id"])
assert mia["video_url"] and mia["nota"] == "Dietro la chiesa", mia
print("7. nel cruscotto: coda 'nuova' contiene", mia["id"], "con nota e video")

ok(c.patch(f"/localita/{casa['id']}", json={"avvisi_attivi": False}))
assert not [a for a in ok(c.get(f"/utenti/{uid}/avvisi")) if a["localita_nome"] == "Casa"]
ok(c.delete(f"/localita/{terreno['id']}"), 204)
print("8. modifica e cancellazione localita")

print("9. ricerca:", [x["nome"] for x in ok(c.get("/cerca", params={"q": "Serramanna"}))][:2],
      "| luogo:", ok(c.get("/luogo", params={"lat": SERRAMANNA[0], "lon": SERRAMANNA[1]})))

ok(c.post(f"/segnalazioni/{r['id']}/archivia"))
print("OK: tutto verificato (segnalazione di prova archiviata)")
