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
