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

export type Utente = { id: number; nome: string; comune: string; punti: number }
export type Segnalazione = {
  id: number; utente_id: number; tipo: 'fuoco' | 'area_a_rischio'; lat: number; lon: number
  foto_url: string | null; priorita: number; motivazioni: string[]; stato: string; creata_il: string
}
export type Rischio = { valore: number; livello: 'basso' | 'medio' | 'alto'; meteo: unknown }

export const coloreAlta = '#dc2626'
export const coloreMedia = '#f97316'
export const coloreBassa = '#16a34a'
export const colorePriorita = (p: number) => (p >= 60 ? coloreAlta : p >= 30 ? coloreMedia : coloreBassa)
export const etichettaPriorita = (p: number) => (p >= 60 ? 'Alta' : p >= 30 ? 'Media' : 'Bassa')

export const stileOsm = {
  version: 8 as const,
  sources: {
    osm: {
      type: 'raster' as const,
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster' as const, source: 'osm' }],
}
