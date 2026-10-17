// Dashboard COP: tipi, livelli del bollettino CFD, geometria minima lato client (piano 2026-10-17-dashboard-cop).
import type { Tema } from './useTema'

export type LivelloCfd = 'verde' | 'arancione' | 'rosso'
export type Quote = { verde: number; arancione: number; rosso: number; massimo: LivelloCfd }
export type Bollettino = { simulato: boolean; fonte: string; valido_per: string; emesso_il: string; per_area: Record<string, Quote>; zone: any }
export type AreaCop = { id: string; nome: string; sede: [number, number]; comuni: number; bbox: [number, number, number, number]; geometria: any }
export type Incendio = {
  id: string; nome: string; comune: string; area: string; stato: 'attivo' | 'spento'; inizio: string; spento_il: string | null
  ettari: number; fronte_m: number; centro: [number, number]; origine: 'simulato' | 'segnalazione'; segnalazione_id?: number
}
export type Statistiche = { area: string; mesi_media: number[]; mesi_2025: number[]; anni: { anno: number; incendi: number; ettari: number }[] }

export const LIVELLI_CFD: Record<LivelloCfd, { etichetta: string; breve: string; css: string }> = {
  verde: { etichetta: 'Pericolo basso', breve: 'Verde', css: 'var(--allerta-verde)' },
  arancione: { etichetta: 'Pericolo medio', breve: 'Arancione', css: 'var(--allerta-arancione)' },
  rosso: { etichetta: 'Pericolo alto', breve: 'Rosso', css: 'var(--allerta-rosso)' },
}
// stessi valori dei token --allerta-* (MapLibre vuole colori, non variabili CSS)
export const coloriAllerta = (t: Tema): Record<LivelloCfd, string> => t === 'scuro'
  ? { verde: '#3fb37f', arancione: '#ff9a3c', rosso: '#ff4d4d' }
  : { verde: '#2f8f63', arancione: '#d9700b', rosso: '#cf2e2e' }

// ---------------------------------------------------------------- geometria

const RAD = Math.PI / 180
export function distanzaKm(a: [number, number], b: [number, number]) {
  const dLat = (b[1] - a[1]) * RAD, dLon = (b[0] - a[0]) * RAD
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * RAD) * Math.cos(b[1] * RAD) * Math.sin(dLon / 2) ** 2
  return 12742 * Math.asin(Math.sqrt(h))
}

function dentroAnello(p: [number, number], anello: number[][]) {
  let dentro = false
  for (let i = 0, j = anello.length - 1; i < anello.length; j = i++) {
    const [xi, yi] = anello[i]!, [xj, yj] = anello[j]!
    if ((yi! > p[1]) !== (yj! > p[1]) && p[0] < ((xj! - xi!) * (p[1] - yi!)) / (yj! - yi!) + xi!) dentro = !dentro
  }
  return dentro
}
export function dentro(p: [number, number], g: any): boolean {
  if (!g) return false
  const poligoni = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : []
  return poligoni.some((pol: number[][][]) => dentroAnello(p, pol[0]!) && !pol.slice(1).some((buco) => dentroAnello(p, buco)))
}

// Cerchio geodetico approssimato (raggio d'azione delle vedette)
export function cerchio(c: [number, number], km: number, passi = 64) {
  const anello: [number, number][] = []
  for (let i = 0; i <= passi; i++) {
    const t = (2 * Math.PI * i) / passi
    anello.push([c[0] + (km / (111.32 * Math.cos(c[1] * RAD))) * Math.cos(t), c[1] + (km / 110.57) * Math.sin(t)])
  }
  return { type: 'Polygon', coordinates: [anello] }
}

// Maschera: tutto il mondo tranne l'area scelta (buchi = anelli esterni dell'area)
export function maschera(g: any) {
  const poligoni = g?.type === 'Polygon' ? [g.coordinates] : g?.type === 'MultiPolygon' ? g.coordinates : []
  const mondo = [[-30, 20], [40, 20], [40, 60], [-30, 60], [-30, 20]]
  return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [mondo, ...poligoni.map((p: any) => [...p[0]].reverse())] } }
}

// ---------------------------------------------------------------- formati

export const fmtOre = (iso: string | null, ora = Date.now()) => {
  if (!iso) return ''
  const min = Math.max(0, Math.round((ora - new Date(iso).getTime()) / 60000))
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  return h < 48 ? `${h} h ${String(min % 60).padStart(2, '0')}` : `${Math.round(h / 24)} giorni`
}
export const fmtNum = (n: number, cifre = 0) => n.toLocaleString('it-IT', { maximumFractionDigits: cifre, minimumFractionDigits: cifre })
export const fmtPct = (q: number) => `${Math.round(q * 100)}%`
export const fmtGiorno = (iso: string) => new Date(iso).toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' })

// Tempo stimato: strada (fattore di tortuosita' 1,35 a 55 km/h) o volo diretto (elicottero 220 km/h, Canadair 300)
export function stimaArrivo(km: number, mezzo: { categoria: string; tipo: string }) {
  const min = mezzo.categoria === 'terra' ? (km * 1.35) / 55 * 60 : km / (mezzo.tipo.startsWith('Canadair') ? 300 : 220) * 60 + 4
  return Math.max(2, Math.round(min))
}

// Mezzi liberi: in base o in pattuglia (possono essere dirottati)
export const MEZZO_LIBERO = ['In base', 'Pattuglia', 'Ricognizione']
export const MEZZO_IMPEGNATO = ['In movimento', 'In volo', 'Sul posto', 'Lancio', 'Carico acqua']

// ---------------------------------------------------------------- segnalazioni

export type FotoValutata = { url: string; nome: string; pertinenza: number; motivo: string; segnalazione: number }

/*
  Selezione delle foto pertinenti: SIMULATA. In produzione un modello di visione (non implementato da noi)
  scarta foto non utili (barbecue, selfie, fumo urbano). Qui: tabella per le foto della demo, valore stabile
  derivato dal nome per le altre.
*/
const AI_DEMO: Record<string, [number, string]> = {
  'demo-cop-fiamme-1.jpg': [0.97, 'Fiamme su vegetazione, fronte visibile'],
  'demo-cop-fiamme-2.jpg': [0.94, 'Fiamme e fumo denso'],
  'demo-cop-fiamme-3.jpg': [0.95, 'Fronte di fiamma su versante boscato'],
  'demo-cop-fumo-1.jpg': [0.81, 'Colonna di fumo su rilievi'],
  'demo-cop-fumo-2.jpg': [0.88, 'Colonna di fumo scuro, origine visibile'],
  'demo-cop-fumo-3.jpg': [0.84, 'Fumo su crinale, distanza media'],
  'demo-cop-cagliari-2.jpg': [0.79, 'Fumo sopra le colline'],
  'demo-cop-cagliari-1.jpg': [0.46, 'Fumo molto lontano, dettaglio scarso'],
  'demo-cop-barbecue.jpg': [0.11, 'Fuoco controllato in braciere, vegetazione non coinvolta'],
}
export function valutaFoto(url: string, segnalazione: number): FotoValutata {
  const nome = url.split('/').pop() ?? url
  const demo = AI_DEMO[nome]
  if (demo) return { url, nome, pertinenza: demo[0], motivo: demo[1], segnalazione }
  // foto fuori dalla demo: il modello simulato non le conosce, restano in primo piano ma senza giudizio
  return { url, nome, pertinenza: SOGLIA_PERTINENZA, motivo: 'Classificazione incerta, guardala tu', segnalazione }
}
export const SOGLIA_PERTINENZA = 0.6

// Segnalazioni vicine (entro 2,5 km) nello stesso gruppo: il capogruppo e' la piu' prioritaria
export function raggruppa<T extends { id: number; lat: number; lon: number; priorita: number }>(lista: T[], km = 2.5) {
  const gruppi: T[][] = []
  for (const s of [...lista].sort((a, b) => b.priorita - a.priorita)) {
    const g = gruppi.find((g) => distanzaKm([g[0]!.lon, g[0]!.lat], [s.lon, s.lat]) <= km)
    if (g) g.push(s)
    else gruppi.push([s])
  }
  return gruppi
}
