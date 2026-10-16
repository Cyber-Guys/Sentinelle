from sentinelle.incendi_attivi import _area, raggruppa


def test_vicini_uniti_lontano_separato():
    # 0 e 1 a ~400 m, 2 a ~600 m da 1 (catena), 3 a ~10 km
    punti = [(40.0, 9.0), (40.0036, 9.0), (40.0090, 9.0), (40.1, 9.0)]
    gruppi = sorted(sorted(g) for g in raggruppa(punti))
    assert gruppi == [[0, 1, 2], [3]]


def test_area_pixel_singolo():
    _, ettari, _, _ = _area([(40.0, 9.0)])
    assert 13.5 < ettari < 14.6  # 375 m x 375 m = 14,06 ha
