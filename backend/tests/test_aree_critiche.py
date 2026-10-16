from sentinelle.aree_critiche import raggruppa


def test_raggruppa_contigue_e_scarta_isolate_non_molto_alte():
    celle = [{"i": 0, "j": 0, "valore": 0.65}, {"i": 1, "j": 1, "valore": 0.68},
             {"i": 5, "j": 5, "valore": 0.75}, {"i": 9, "j": 9, "valore": 0.62}]
    g = raggruppa(celle)
    assert [len(x) for x in g] == [1, 2]
    assert g[0][0]["valore"] == 0.75
