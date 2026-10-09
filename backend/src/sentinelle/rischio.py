from .fonti.meteo import Meteo


def _n(x: float) -> float:
    return max(0.0, min(1.0, x))


def rischio_meteo(m: Meteo) -> float:
    """0..1: raffiche, aria secca, caldo, giorni senza pioggia."""
    return round(0.3 * _n(m.raffiche_kmh / 60) + 0.3 * _n((100 - m.umidita) / 70)
                 + 0.2 * _n((m.temperatura - 10) / 25) + 0.2 * _n(m.giorni_senza_pioggia / 15), 3)
