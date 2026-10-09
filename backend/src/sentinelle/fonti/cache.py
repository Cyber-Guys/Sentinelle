import time

_cache: dict[str, tuple[float, object]] = {}
DURATA_S = 600  # 10 minuti


def con_cache(chiave: str, carica):
    """Valore in cache se fresco; su errore l'ultimo valore valido, altrimenti None."""
    ora = time.time()
    voce = _cache.get(chiave)
    if voce and ora - voce[0] < DURATA_S:
        return voce[1]
    try:
        valore = carica()
    except Exception:
        return voce[1] if voce else None
    _cache[chiave] = (ora, valore)
    return valore
