import { Flame, CloudFog, TriangleAlert } from '@lucide/vue'
import type { Component } from 'vue'
import type { Tema } from '~/composables/useTema'

// "Waze per gli incendi": tipi, livelli di affidabilita', stati ufficiali (sempre colore + parola + icona)
export type TipoSegnalazione = 'fuoco' | 'fumo' | 'area_a_rischio'
export type LivelloAff = 'da_verificare' | 'probabile' | 'comunita' | 'operatori'
export type StatoUfficiale = 'in_verifica' | 'allertati' | 'mezzi_sul_posto' | 'spento'
export type FattoreAff = { chiave: string; etichetta: string; contributo: number }
export type Condivisa = {
  id: number; tipo: TipoSegnalazione; lat: number; lon: number; creata_il: string; aggiornata_il: string
  stato_ufficiale: StatoUfficiale
  affidabilita: { valore: number; livello: LivelloAff; etichetta: string; fattori: FattoreAff[] }
  conferme: number; smentite: number; probabilmente_spento: boolean; foto_url: string | null
  mia: boolean; mio_voto: 'ancora' | 'finito' | null; distanza_m?: number
}

export const TIPI: Record<TipoSegnalazione, { etichetta: string; breve: string; nota: string; icona: Component; colore: string }> = {
  fuoco: { etichetta: 'Fuoco', breve: 'fuoco', nota: 'Fiamme visibili', icona: Flame, colore: 'var(--brace)' },
  fumo: { etichetta: 'Fumo', breve: 'fumo', nota: 'Colonna o odore', icona: CloudFog, colore: 'var(--fumo)' },
  area_a_rischio: { etichetta: 'Area a rischio', breve: 'area a rischio', nota: 'Sterpaglie, rifiuti', icona: TriangleAlert, colore: 'var(--ambra)' },
}
export const ORDINE_TIPI = Object.keys(TIPI) as TipoSegnalazione[]

export const LIVELLI_AFF: Record<LivelloAff, { etichetta: string; colore: string }> = {
  da_verificare: { etichetta: 'Da verificare', colore: 'var(--testo-3)' },
  probabile: { etichetta: 'Probabile', colore: 'var(--ambra)' },
  comunita: { etichetta: 'Confermata dalla comunità', colore: 'var(--cielo)' },
  operatori: { etichetta: 'Confermata dagli operatori', colore: 'var(--macchia)' },
}
export const STATI_UFF: Record<StatoUfficiale, { etichetta: string; colore: string }> = {
  in_verifica: { etichetta: 'In verifica', colore: 'var(--testo-2)' },
  allertati: { etichetta: 'Operatori allertati', colore: 'var(--ambra)' },
  mezzi_sul_posto: { etichetta: 'Mezzi sul posto', colore: 'var(--brace)' },
  spento: { etichetta: 'Spento', colore: 'var(--macchia)' },
}
export const RAGGIO_VOTO_M = 2000

// colori per la mappa (MapLibre vuole valori): stessi toni dei token
export function coloriTipi(t: Tema): Record<TipoSegnalazione, string> {
  const s = t === 'scuro'
  return {
    fuoco: s ? '#ff6a2b' : '#e8351f', fumo: s ? '#a3b3c4' : '#566676', area_a_rischio: s ? '#f5b83d' : '#d99a1e',
  }
}

export function distanzaM(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  return Math.hypot((a.lon - b.lon) * 111320 * Math.cos(((a.lat + b.lat) / 2) * Math.PI / 180), (a.lat - b.lat) * 110570)
}
export const distanzaTesto = (m: number) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toLocaleString('it-IT', { maximumFractionDigits: 1 })} km`)
export function daQuanto(iso: string) {
  const min = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  if (min < 1) return 'adesso'
  if (min < 60) return `${min} min fa`
  const h = Math.floor(min / 60)
  return h < 24 ? `${h} h fa` : `${Math.floor(h / 24)} g fa`
}
