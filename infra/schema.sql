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
-- rischio di oggi: celle ~2 km precalcolate da scripts/prepara_celle.py
CREATE TABLE IF NOT EXISTS cella (id serial PRIMARY KEY, i int NOT NULL, j int NOT NULL,
  lon double precision NOT NULL, lat double precision NOT NULL, geom geometry(Polygon,4326) NOT NULL,
  storico double precision NOT NULL DEFAULT 0, pericolo double precision NOT NULL DEFAULT 0, UNIQUE (i, j));
CREATE INDEX IF NOT EXISTS cella_geom_idx ON cella USING gist (geom);
-- missioni mirate dal rischio: generate per utente e giorno, completamento = mappatura 'sterpaglie'
CREATE TABLE IF NOT EXISTS missione_mirata (id serial PRIMARY KEY, utente_id int NOT NULL REFERENCES utente,
  cella_id int REFERENCES cella, geom geometry(Point,4326) NOT NULL, titolo text NOT NULL, motivo text NOT NULL,
  punti int NOT NULL, valore_rischio double precision NOT NULL, creata_il timestamptz NOT NULL DEFAULT now(),
  scade_il timestamptz NOT NULL, completata_il timestamptz,
  completamento_id int REFERENCES missione_completata ON DELETE SET NULL);
-- esito del sopralluogo mirato: pulita | sterpaglie | rifiuti (null per le mappature normali)
ALTER TABLE missione_mirata ADD COLUMN IF NOT EXISTS esito text;
ALTER TABLE missione_completata ADD COLUMN IF NOT EXISTS esito text;
-- scomposizione della priorita' per fattore (vuota per le segnalazioni precedenti)
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS fattori jsonb NOT NULL DEFAULT '[]'::jsonb;
-- storico: data di valutazione e punti guadagnati con la segnalazione
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS valutata_il timestamptz;
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS punti_ottenuti int NOT NULL DEFAULT 0;
-- waze per gli incendi: tre tipi (focus sul fuoco, 2026-10-16), stato ufficiale per i cittadini, voti (vedi piano 2026-10-16)
ALTER TABLE segnalazione DROP CONSTRAINT IF EXISTS segnalazione_tipo_check;
DELETE FROM segnalazione WHERE tipo NOT IN ('fuoco','fumo','area_a_rischio');
ALTER TABLE segnalazione ADD CONSTRAINT segnalazione_tipo_check
  CHECK (tipo IN ('fuoco','fumo','area_a_rischio'));
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS stato_ufficiale text NOT NULL DEFAULT 'in_verifica'
  CHECK (stato_ufficiale IN ('in_verifica','allertati','mezzi_sul_posto','spento'));
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS aggiornata_il timestamptz NOT NULL DEFAULT now();
CREATE TABLE IF NOT EXISTS voto_segnalazione (
  id serial PRIMARY KEY, segnalazione_id int NOT NULL REFERENCES segnalazione ON DELETE CASCADE,
  utente_id int NOT NULL REFERENCES utente, voto text NOT NULL CHECK (voto IN ('ancora','finito')),
  geom geometry(Point,4326) NOT NULL, creato_il timestamptz NOT NULL DEFAULT now(),
  UNIQUE (segnalazione_id, utente_id));
-- eventi live: notifica sul canale 'sentinelle' (idempotente)
CREATE OR REPLACE FUNCTION notifica_sentinelle() RETURNS trigger AS $$
BEGIN
  IF TG_TABLE_NAME = 'segnalazione' AND TG_OP = 'INSERT' THEN
    PERFORM pg_notify('sentinelle', json_build_object('tipo', 'segnalazione_nuova', 'id', NEW.id,
      'utente_id', NEW.utente_id, 'priorita', NEW.priorita)::text);
  ELSIF TG_TABLE_NAME = 'segnalazione' AND TG_NAME = 'segnalazione_aggiornata_notifica' THEN
    PERFORM pg_notify('sentinelle', json_build_object('tipo', 'segnalazione_aggiornata', 'id', NEW.id,
      'utente_id', NEW.utente_id, 'stato_ufficiale', NEW.stato_ufficiale)::text);
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
DROP TRIGGER IF EXISTS segnalazione_aggiornata_notifica ON segnalazione;
CREATE TRIGGER segnalazione_aggiornata_notifica AFTER UPDATE OF stato_ufficiale, aggiornata_il ON segnalazione
  FOR EACH ROW WHEN (OLD.stato_ufficiale IS DISTINCT FROM NEW.stato_ufficiale
    OR OLD.aggiornata_il IS DISTINCT FROM NEW.aggiornata_il) EXECUTE FUNCTION notifica_sentinelle();
DROP TRIGGER IF EXISTS mappatura_nuova_notifica ON missione_completata;
CREATE TRIGGER mappatura_nuova_notifica AFTER INSERT ON missione_completata
  FOR EACH ROW WHEN (NEW.geom IS NOT NULL) EXECUTE FUNCTION notifica_sentinelle();
-- webapp cittadino: telefono, media/nota/direzione delle segnalazioni, localita' monitorate (piano 2026-10-16-webapp-cittadino)
ALTER TABLE utente ADD COLUMN IF NOT EXISTS telefono text;
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS video text;
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS nota text;
ALTER TABLE segnalazione ADD COLUMN IF NOT EXISTS direzione int;
CREATE TABLE IF NOT EXISTS localita (id serial PRIMARY KEY, utente_id int NOT NULL REFERENCES utente ON DELETE CASCADE,
  nome text NOT NULL, tipo text NOT NULL DEFAULT 'altro' CHECK (tipo IN ('casa','terreno','vigna','altro')),
  indirizzo text, geom geometry(Point,4326) NOT NULL, avvisi_attivi boolean NOT NULL DEFAULT true,
  avvisi_tipi text[] NOT NULL DEFAULT '{fuoco,fumo}', raggio_km int NOT NULL DEFAULT 5 CHECK (raggio_km IN (2,5,10)),
  urgenza text NOT NULL DEFAULT 'urgenti_importanti' CHECK (urgenza IN ('urgenti','urgenti_importanti','tutti')),
  creata_il timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS localita_utente_idx ON localita (utente_id);
