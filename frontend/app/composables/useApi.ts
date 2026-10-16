export function useApi() {
  const base = useRuntimeConfig().public.apiBaseUrl as string

  async function chiama<T>(percorso: string, opzioni: RequestInit = {}): Promise<T> {
    const r = await fetch(base + percorso, opzioni)
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
    return r.json()
  }

  const urlFoto = (u: string | null) => (u ? (u.startsWith('http') ? u : base + u) : null)

  return { base, chiama, urlFoto }
}

// Messaggio per le persone, non per gli sviluppatori: rete giu' o server in errore diventano una frase sola.
export function messaggioErrore(e: unknown, azione = 'caricare i dati') {
  const m = String((e as Error)?.message ?? '')
  if (/^4\d\d/.test(m) && !/^40[48]/.test(m)) return `Non è stato possibile ${azione}: richiesta non valida.`
  return `Non riusciamo a ${azione}. Controlla la connessione e riprova.`
}

export type Livello = { nome: string; soglia: number; prossima_soglia: number | null; progresso: number }
export type Utente = { id: number; nome: string; comune: string; punti: number; livello?: Livello }
export type Missione = {
  id: number; codice: string; titolo: string; descrizione: string; punti: number
  tipo: 'quiz' | 'posizione' | 'esplora'; disponibile: boolean; motivo: string | null
}
export type MissioneMirata = {
  id: number; titolo: string; motivo: string; punti: number; valore_rischio: number
  livello_rischio: 'medio' | 'alto' | 'molto alto'; lon: number; lat: number; distanza_km: number
  scade_il: string; completata: boolean
}
export type DomandaQuiz = { indice: number; domanda: string; opzioni: string[] }
export type EsitoQuiz = { indice: number; giusta: boolean; corretta: number; spiegazione: string }
export type EsitoMissione = { punti_ottenuti: number; punti: number; livello: Livello; esiti?: EsitoQuiz[] }
export type RigaComune = { comune: string; punti: number; utenti: number }
export type RigaUtente = { nome: string; punti: number; livello: Livello | string }

// centri approssimativi dei comuni di demo (per mappa e statistiche)
export const CENTRI_COMUNI: Record<string, [number, number]> = {
  SERRAMANNA: [8.92, 39.42], VILLASOR: [8.94, 39.38], VILLACIDRO: [8.74, 39.46],
  SAMASSI: [8.91, 39.49], SERRENTI: [8.92, 39.47], SANLURI: [8.90, 39.56],
}
export type Segnalazione = {
  id: number; utente_id: number; tipo: 'fuoco' | 'area_a_rischio'; lat: number; lon: number
  foto_url: string | null; priorita: number; motivazioni: string[]; fattori: Fattore[]; comune: string | null
  stato: StatoSegnalazione; creata_il: string; valutata_il?: string | null; punti_ottenuti?: number
}
export type StatoSegnalazione = 'nuova' | 'confermata' | 'archiviata'
// stato della segnalazione per le persone: sempre colore + parola
export const STATI: Record<StatoSegnalazione, { etichetta: string; colore: string }> = {
  nuova: { etichetta: 'In valutazione', colore: 'var(--ambra)' },
  confermata: { etichetta: 'Confermata', colore: 'var(--macchia)' },
  archiviata: { etichetta: 'Falso allarme', colore: 'var(--testo-3)' },
}
export const dataOra = (iso: string) => new Date(iso).toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
// un termine della priorita': valore 0..1, peso effettivo (rinormalizzato), contributo in punti 0..100
export type Fattore = {
  chiave: 'hotspot' | 'meteo' | 'suolo' | 'pericolo' | 'vicine' | 'storico'; etichetta: string
  valore: number; peso: number; contributo: number; testo: string; disponibile: boolean
}
// 'SAN GAVINO MONREALE' -> 'San Gavino Monreale', "SANT'ANTIOCO" -> "Sant'Antioco"
export const nomeComune = (c?: string | null) => (c ?? '').toLowerCase().replace(/(^|[\s'-])(\p{L})/gu, (_, a, b) => a + b.toUpperCase())
export type Rischio = { valore: number; livello: 'basso' | 'medio' | 'alto' | 'molto alto'; meteo: unknown }

export const coloreAlta = '#ff6a2b'
export const coloreMedia = '#f5b83d'
export const coloreBassa = '#3fb37f'
export const colorePriorita = (p: number) => (p >= 60 ? coloreAlta : p >= 30 ? coloreMedia : coloreBassa)
// stessa scala come token CSS (segue il tema)
export const varPriorita = (p: number) => (p >= 60 ? 'var(--brace)' : p >= 30 ? 'var(--ambra)' : 'var(--macchia)')
export const etichettaPriorita = (p: number) => (p >= 60 ? 'Alta' : p >= 30 ? 'Media' : 'Bassa')
// aree critiche di oggi (GET /aree-critiche): zone contigue a rischio alto, con motivi dai dati
export type AreaCritica = {
  id: number; livello: 'alto' | 'molto_alto'; indice: number; centro: { lat: number; lon: number }
  area: any; comuni: string[]; nome: string; motivo: string; picco: { dalle: string; alle: string }
  fattori: { chiave: string; etichetta: string; valore: number; testo: string }[]
  punto_peggiore: { lat: number; lon: number }; invaso: { nome: string; distanza_km: number; riempimento: number | null } | null
}
export type AreeCritiche = { aggiornato_il: string; meteo_simulato: boolean; aree: AreaCritica[] }
export const LIVELLI_AREA = { molto_alto: { etichetta: 'Molto alto', colore: 'var(--brace)' }, alto: { etichetta: 'Alto', colore: 'var(--ambra)' } } as const
