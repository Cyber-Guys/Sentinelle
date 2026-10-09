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
  foto_url: string | null; priorita: number; motivazioni: string[]; stato: string; creata_il: string
  punti_ottenuti?: number
}
export type Rischio = { valore: number; livello: 'basso' | 'medio' | 'alto'; meteo: unknown }

export const coloreAlta = '#ff6a2b'
export const coloreMedia = '#f5b83d'
export const coloreBassa = '#3fb37f'
export const colorePriorita = (p: number) => (p >= 60 ? coloreAlta : p >= 30 ? coloreMedia : coloreBassa)
// stessa scala come token CSS (segue il tema)
export const varPriorita = (p: number) => (p >= 60 ? 'var(--brace)' : p >= 30 ? 'var(--ambra)' : 'var(--macchia)')
export const etichettaPriorita = (p: number) => (p >= 60 ? 'Alta' : p >= 30 ? 'Media' : 'Bassa')
