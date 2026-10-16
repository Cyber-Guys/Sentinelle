from sentinelle.missioni_mirate import km, livello, scegli


def test_scegli_rischio_alto_e_celle_distanti():
    celle = [{"lon": 9.0, "lat": 39.0, "valore": 0.8}, {"lon": 9.01, "lat": 39.0, "valore": 0.79},
             {"lon": 9.1, "lat": 39.0, "valore": 0.6}, {"lon": 9.2, "lat": 39.0, "valore": 0.5},
             {"lon": 9.3, "lat": 39.0, "valore": 0.4}]
    s = scegli(celle, n=3, distanza_min=4)
    assert [c["valore"] for c in s] == [0.8, 0.6, 0.5]
    assert all(km(a["lon"], a["lat"], b["lon"], b["lat"]) >= 4 for a in s for b in s if a is not b)
    assert [livello(v)[1] for v in (0.75, 0.65, 0.5)] == [40, 30, 20]
