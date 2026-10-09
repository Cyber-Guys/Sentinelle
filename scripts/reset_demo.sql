-- Riporta la demo allo stato iniziale: nessuna segnalazione, punti a zero.
-- Uso: docker exec -i infra-db-1 psql -U sentinelle < scripts/reset_demo.sql
TRUNCATE segnalazione RESTART IDENTITY;
UPDATE utente SET punti = 0;
