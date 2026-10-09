"""Mappatura dei campi dei perimetri incendi: i nomi cambiano da un anno all'altro."""
import re
from datetime import date


def primo(p, chiavi):
    for k in chiavi:
        if p.get(k) not in (None, ""):
            return p[k]


def numero(v, div=1):
    try:
        return float(v) / div
    except (TypeError, ValueError):
        return None


def data(v):
    # i formati cambiano da un anno all'altro: gg/mm/aaaa, aaaa-mm-gg, aaaa/mm/gg, con o senza "Z"
    m = re.match(r"(\d{4})[-/](\d{2})[-/](\d{2})", str(v or ""))
    if m:
        return date(*map(int, m.groups()))
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", str(v or ""))
    return date(int(m[3]), int(m[2]), int(m[1])) if m else None


def ettari_totali(p):
    tot = numero(primo(p, ["totale_ha", "ha_totale", "ha_totali", "sup_tot_ha", "area"]))
    if tot is None:
        tot = numero(primo(p, ["totale_mq", "mq_totale", "mq_totali", "sup_tot_mq", "sup_tot"]), 10000)
    return tot


def ettari_bosco(p):
    bosco = numero(primo(p, ["bosco_ha", "ha_bosco"]))
    if bosco is None:
        bosco = numero(primo(p, ["bosco_mq", "mq_bosco", "m2_bosco", "sup_bosco"]), 10000)
    return bosco


def comune(p):
    c = primo(p, ["comune"])
    return c.upper() if c else None


def data_incendio(p):
    return data(primo(p, ["data", "data_ince", "dt_ince"]))
