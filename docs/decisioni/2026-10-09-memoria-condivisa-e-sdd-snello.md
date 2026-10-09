# Memoria condivisa e SDD snello

**Data:** 2026-10-09
**Stato:** accettata

## Decisione

- La memoria del progetto vive nel repository: `AGENTS.md` come fonte unica
  delle regole, `CLAUDE.md` e `GEMINI.md` la importano, `STATO.md` come
  fotografia corrente, `docs/` per decisioni, piani, specifiche, esperimenti e
  pitch.
- Implementazione con `superpowers:subagent-driven-development` minimale:
  implementer sequenziali su modello medio, nessun reviewer agent, un solo
  controllo finale del controller.
- Una verifica eseguibile per consegna, niente test estesi.

## Motivazione

Hackathon a squadre con agenti diversi (Claude Code, Codex, ...): serve una
memoria leggibile da tutti e versionata. Il tempo e' il vincolo principale;
revisioni multiple e test estesi non migliorano la demo.

## Conseguenze

- I difetti non visibili nella demo si accettano.
- Decisioni nominate per data e slug per evitare collisioni tra branch.
