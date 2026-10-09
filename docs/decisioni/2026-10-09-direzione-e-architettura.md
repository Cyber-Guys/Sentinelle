# Direzione di progetto e architettura

**Data:** 2026-10-09
**Stato:** accettata

## Decisione

- Challenge 2 e 3 fuse: segnalazione partecipata con verifica incrociata +
  gamification basata su missioni di prevenzione.
- Utente principale: comunita' locali. Destinatario: cruscotto operatori.
- Demo su dati live con segnalazioni simulate.
- Stack: Nuxt 4 (stack di cia-sardegna-learning) + FastAPI + PostgreSQL/PostGIS
  in docker compose.

Specifica: `docs/specifiche/2026-10-09-sentinelle-incendi.md`.

## Motivazione

Copre due challenge, usa le fonti piu' ricche (perimetri CFVA, FIRMS, EFFIS,
Open-Meteo) e nessuna app esistente trovata unisce segnalazione, satellite,
rischio e gamification (`docs/dominio/fonti-incendi-extra.md`). PostGIS
scelto rispetto a SQLite per le query geografiche native, accettando il costo
di Docker.

## Conseguenze

- Dati geografici precaricati e versionati: il WFS regionale e' instabile.
- Ogni membro deve poter avviare l'ambiente con un solo `docker compose up`.
