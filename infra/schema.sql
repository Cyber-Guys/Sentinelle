CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE comune (id serial PRIMARY KEY, nome text NOT NULL, geom geometry(MultiPolygon,4326));
CREATE TABLE incendio_storico (id serial PRIMARY KEY, cod_incend text, anno int, data date,
  comune text, ettari_totali double precision, ettari_bosco double precision,
  tipologia text, geom geometry(MultiPolygon,4326),
  geom_semplice geometry(MultiPolygon,4326));
CREATE TABLE pericolo_aib (id serial PRIMARY KEY, classe text, geom geometry(MultiPolygon,4326));
CREATE TABLE utente (id serial PRIMARY KEY, nome text NOT NULL, comune_id int REFERENCES comune, punti int NOT NULL DEFAULT 0);
CREATE TABLE segnalazione (id serial PRIMARY KEY, utente_id int REFERENCES utente,
  tipo text NOT NULL CHECK (tipo IN ('fuoco','area_a_rischio')),
  geom geometry(Point,4326) NOT NULL, foto text, priorita int NOT NULL,
  motivazioni jsonb NOT NULL, stato text NOT NULL DEFAULT 'nuova'
  CHECK (stato IN ('nuova','confermata','archiviata')), creata_il timestamptz NOT NULL DEFAULT now());
CREATE INDEX ON comune USING gist (geom);
CREATE INDEX ON incendio_storico USING gist (geom);
CREATE INDEX ON incendio_storico USING gist (geom_semplice);
CREATE INDEX ON pericolo_aib USING gist (geom);
CREATE INDEX ON segnalazione USING gist (geom);
-- gioco: missioni e completamenti (idempotente; eseguita anche da carica_dati, semina_demo e avvio app)
CREATE TABLE IF NOT EXISTS missione (id serial PRIMARY KEY, codice text UNIQUE NOT NULL,
  titolo text NOT NULL, descrizione text NOT NULL, punti int NOT NULL,
  tipo text NOT NULL CHECK (tipo IN ('quiz','posizione','esplora')));
CREATE TABLE IF NOT EXISTS missione_completata (id serial PRIMARY KEY,
  utente_id int NOT NULL REFERENCES utente, missione_id int NOT NULL REFERENCES missione,
  punti int NOT NULL, geom geometry(Point,4326), foto text,
  completata_il timestamptz NOT NULL DEFAULT now());
-- scomposizione della priorita' per fattore (vuota per le segnalazioni precedenti)
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS fattori jsonb NOT NULL DEFAULT '[]'::jsonb;
-- storico: data di valutazione e punti guadagnati con la segnalazione
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS valutata_il timestamptz;
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS punti_ottenuti int NOT NULL DEFAULT 0;
-- eventi live: notifica sul canale 'sentinelle' (idempotente)
CREATE OR REPLACE FUNCTION notifica_sentinelle() RETURNS trigger AS $$
BEGIN
  IF TG_TABLE_NAME = 'segnalazione' AND TG_OP = 'INSERT' THEN
    PERFORM pg_notify('sentinelle', json_build_object('tipo', 'segnalazione_nuova', 'id', NEW.id,
      'utente_id', NEW.utente_id, 'priorita', NEW.priorita)::text);
  ELSIF TG_TABLE_NAME = 'segnalazione' THEN
    PERFORM pg_notify('sentinelle', json_build_object('tipo', 'segnalazione_valutata', 'id', NEW.id,
      'utente_id', NEW.utente_id, 'stato', NEW.stato)::text);
  ELSE
    PERFORM pg_notify('sentinelle', json_build_object('tipo', 'mappatura_nuova', 'id', NEW.id,
      'utente_id', NEW.utente_id)::text);
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS segnalazione_nuova_notifica ON segnalazione;
CREATE TRIGGER segnalazione_nuova_notifica AFTER INSERT ON segnalazione
  FOR EACH ROW EXECUTE FUNCTION notifica_sentinelle();
DROP TRIGGER IF EXISTS segnalazione_valutata_notifica ON segnalazione;
CREATE TRIGGER segnalazione_valutata_notifica AFTER UPDATE OF stato ON segnalazione
  FOR EACH ROW WHEN (OLD.stato IS DISTINCT FROM NEW.stato) EXECUTE FUNCTION notifica_sentinelle();
DROP TRIGGER IF EXISTS mappatura_nuova_notifica ON missione_completata;
CREATE TRIGGER mappatura_nuova_notifica AFTER INSERT ON missione_completata
  FOR EACH ROW WHEN (NEW.geom IS NOT NULL) EXECUTE FUNCTION notifica_sentinelle();
