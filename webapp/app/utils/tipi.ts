// Contratti con il backend: docs/specifiche/2026-10-16-webapp-cittadino.md

export type TipoSegnalazione = 'fuoco' | 'fumo' | 'area_a_rischio'
export type TipoLocalita = 'casa' | 'terreno' | 'vigna' | 'altro'
export type Livello = 'basso' | 'medio' | 'alto' | 'molto alto'
export type Priorita = 'urgente' | 'importante' | 'informazione'
export type Urgenza = 'urgenti' | 'urgenti_importanti' | 'tutti'

export interface Utente {
  id: number
  nome: string
  telefono: string | null
  comune: string | null
  punti: number
  n_segnalazioni: number
  n_con_media: number
}

export interface StatoLocalita {
  livello: Livello
  n_zone: number
  zone: GeoJSON.FeatureCollection
  n_segnalazioni: number
  n_avvisi: number
  priorita_max: Priorita | null
  meteo_simulato: boolean
}

export interface Localita {
  id: number
  utente_id: number
  nome: string
  tipo: TipoLocalita
  indirizzo: string | null
  lat: number
  lon: number
  avvisi_attivi: boolean
  avvisi_tipi: TipoSegnalazione[]
  raggio_km: 2 | 5 | 10
  urgenza: Urgenza
  stato: StatoLocalita
}

export interface Avviso {
  id: string
  priorita: Priorita
  tipo: TipoSegnalazione | 'rischio'
  segnalazione_id: number | null
  titolo: string
  testo: string
  localita_id: number
  localita_nome: string
  distanza_km: number | null
  lat: number
  lon: number
  da_lat: number // posizione del luogo da cui si misura la distanza
  da_lon: number
  creato_il: string | null
}

export interface Condivisa {
  id: number
  tipo: TipoSegnalazione
  lat: number
  lon: number
  creata_il: string
  stato_ufficiale: 'in_verifica' | 'allertati' | 'mezzi_sul_posto' | 'spento'
  conferme: number
  smentite: number
  mia: boolean
  mio_voto: 'ancora' | 'finito' | null
  probabilmente_spento: boolean
}

export interface RigaStorico {
  id: number
  tipo: TipoSegnalazione
  lat: number
  lon: number
  creata_il: string
  foto_url: string | null
  video_url: string | null
  nota: string | null
  direzione: number | null
  stato: 'nuova' | 'confermata' | 'archiviata'
  stato_ufficiale: string
  comune: string | null
  km_casa: number | null
}

export interface Segnalazione {
  id: number
  tipo: TipoSegnalazione
  priorita: number
  motivazioni: string[]
  creata_il: string
  comune: string | null
  nota: string | null
}

export interface Risultato {
  nome: string
  lat: number
  lon: number
  approssimato: boolean
}

export const TIPI: Record<TipoSegnalazione, { nome: string; breve: string; aiuto: string }> = {
  fuoco: { nome: 'Incendio', breve: 'Incendio', aiuto: 'Vedo le fiamme' },
  fumo: { nome: 'Fumo', breve: 'Fumo', aiuto: 'Vedo il fumo, non le fiamme' },
  area_a_rischio: { nome: 'Terreno a rischio', breve: 'Terreno', aiuto: 'Erba secca, rifiuti, cose che bruciano' },
}

export const TIPI_LOCALITA: Record<TipoLocalita, string> = { casa: 'Casa', terreno: 'Terreno', vigna: 'Vigna', altro: 'Altro' }

export const PRIORITA: Record<Priorita, { nome: string; classe: string }> = {
  urgente: { nome: 'Urgente', classe: 'e-brace-pieno' },
  importante: { nome: 'Importante', classe: 'e-ambra' },
  informazione: { nome: 'Informazione', classe: 'e-cielo' },
}

export const LIVELLI: Record<Livello, { nome: string; classe: string }> = {
  basso: { nome: 'Rischio basso', classe: 'e-macchia' },
  medio: { nome: 'Rischio medio', classe: 'e-ambra' },
  alto: { nome: 'Rischio alto', classe: 'e-brace' },
  'molto alto': { nome: 'Rischio molto alto', classe: 'e-brace-pieno' },
}

export const STATI_UFFICIALI: Record<string, string> = {
  in_verifica: 'In verifica', allertati: 'Soccorritori allertati', mezzi_sul_posto: 'Mezzi sul posto', spento: 'Spento',
}
