import tomllib

from sentinelle.config import FILE_PESI
from sentinelle.fonti import Meteo
from sentinelle.rischio import rischio_meteo
from sentinelle.verifica import Contesto, calcola_priorita

PESI = tomllib.loads(FILE_PESI.read_text())
METEO_ESTREMO = Meteo(vento_kmh=50, raffiche_kmh=80, umidita=10, temperatura=40, giorni_senza_pioggia=30)
METEO_CALMO = Meteo(vento_kmh=2, raffiche_kmh=5, umidita=95, temperatura=8, giorni_senza_pioggia=0)


def test_contesto_massimo_priorita_alta():
    c = Contesto(0.0, METEO_ESTREMO, (311, "Boschi di latifoglie"), "Alto", 5, 10)
    assert calcola_priorita(c, PESI).priorita >= 85


def test_contesto_minimo_priorita_bassa():
    c = Contesto(50.0, METEO_CALMO, (112, "Tessuto urbano discontinuo"), "Basso", 0, 0)
    assert calcola_priorita(c, PESI).priorita <= 15


def test_fonte_none_esclusa_e_pesi_rinormalizzati():
    pieno = Contesto(0.0, METEO_ESTREMO, (311, "Boschi"), "Alto", 5, 10)
    senza = Contesto(None, METEO_ESTREMO, (311, "Boschi"), "Alto", 5, 10)
    e = calcola_priorita(senza, PESI)
    assert any("non disponibile" in m for m in e.motivazioni)
    # tutti gli altri termini sono al massimo: con rinormalizzazione resta 100
    assert e.priorita == 100 and calcola_priorita(pieno, PESI).priorita == 100


def test_una_motivazione_per_termine():
    c = Contesto(1.2, METEO_CALMO, (311, "Boschi"), None, 1, 2)
    assert len(calcola_priorita(c, PESI).motivazioni) == 6
    c2 = Contesto(None, None, None, "Medio", 0, 0)
    assert len(calcola_priorita(c2, PESI).motivazioni) == 6
