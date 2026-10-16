from sentinelle.affidabilita import Prove, Voto, affidabilita_utente, probabilmente_spento, punteggio

AUTORE = Voto("ancora", 0.5, 0)


def test_affidabilita_utente():
    assert affidabilita_utente(0, 0) == 0.5
    assert affidabilita_utente(3, 3) == 0.8
    assert affidabilita_utente(0, 2) == 0.25


def test_soglie():
    assert punteggio([AUTORE], Prove(), 0, "fumo").livello == "da_verificare"
    assert punteggio([AUTORE], Prove(hotspot=True), 0, "fumo").livello == "probabile"
    tre = [AUTORE] + [Voto("ancora", 0.75, 0)] * 3
    assert punteggio(tre, Prove(), 0, "fumo").livello == "comunita"
    assert punteggio([AUTORE], Prove(operatore=True), 0, "fumo").livello == "operatori"


def test_decadimento():
    v = punteggio([Voto("ancora", 1.0, 120)], Prove(), 120, "fuoco").valore
    assert v == 0.5
    assert punteggio([Voto("ancora", 1.0, 120)], Prove(), 120, "area_a_rischio").valore > 0.75


def test_voto_pesato_e_spento():
    voti = [AUTORE, Voto("finito", 0.9, 5)]
    assert punteggio(voti, Prove(), 5, "fumo").valore < 0
    assert probabilmente_spento(voti)
    assert not probabilmente_spento([AUTORE, Voto("finito", 0.4, 5)])
    assert not probabilmente_spento([Voto("ancora", 0.5, 60), Voto("finito", 0.9, 90)])
