import numpy as np

from sentinelle.fonti.meteo_orario import Ora
from sentinelle.simulazione import tempi_arrivo

N = 101
C = N // 2


def _arrivo(comb, vento=25.0, da=270.0, ore=3):
    return tempi_arrivo(comb, (C, C), [Ora(vento, da, 30, 0, 30, 40)] * ore, ore * 60)


def test_vento_da_ovest_sposta_a_est():
    b = np.isfinite(_arrivo(np.ones((N, N))))
    colonne = np.nonzero(b)[1]
    assert colonne.mean() > C + 3


def test_mare_non_brucia():
    comb = np.ones((N, N))
    comb[:, C + 5:] = 0.0  # mare a est
    b = np.isfinite(_arrivo(comb))
    assert not b[:, C + 5:].any()


def test_area_cresce_nel_tempo():
    t = _arrivo(np.ones((N, N)), ore=3)
    a = [(t <= h * 60).sum() for h in (1, 2, 3)]
    assert a[0] < a[1] < a[2]
