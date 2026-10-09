-- Riporta la demo allo stato iniziale: nessuna segnalazione ne' missione completata, punti a zero.
-- Poi rilanciare scripts/semina_demo.py per ripopolare la classifica simulata.
-- Uso: docker exec -i infra-db-1 psql -U sentinelle < scripts/reset_demo.sql
TRUNCATE segnalazione, missione_completata RESTART IDENTITY;
UPDATE utente SET punti = 0;
