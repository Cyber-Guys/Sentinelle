// Posizione del telefono. Senza GPS (permesso negato, desktop, nessun segnale) si usa un punto di prova
// dichiarato: `reale` resta falso e l'interfaccia lo dice. Per le prove: ?pos=39.4216,8.9223 fissa il punto.
export const PUNTO_DI_PROVA = { lat: 39.4216, lon: 8.9223 } // Via Roma, Serramanna

interface Posizione { lat: number; lon: number; precisione: number }

let osservatore: number | null = null

export function usePosizione() {
  const pos = useState<Posizione>('pos', () => ({ ...PUNTO_DI_PROVA, precisione: 0 }))
  const reale = useState('pos-reale', () => false)
  const stato = useState<'attesa' | 'ok' | 'negata' | 'assente'>('pos-stato', () => 'attesa')

  function avvia() {
    if (!import.meta.client || osservatore !== null) return
    const forzata = new URLSearchParams(location.search).get('pos')?.split(',').map(Number)
    if (forzata?.length === 2 && forzata.every(Number.isFinite)) {
      pos.value = { lat: forzata[0]!, lon: forzata[1]!, precisione: 20 }
      reale.value = true
      stato.value = 'ok'
      return
    }
    if (!('geolocation' in navigator)) { stato.value = 'assente'; return }
    osservatore = navigator.geolocation.watchPosition(
      (p) => {
        pos.value = { lat: p.coords.latitude, lon: p.coords.longitude, precisione: p.coords.accuracy }
        reale.value = true
        stato.value = 'ok'
      },
      (e) => { stato.value = e.code === 1 ? 'negata' : 'assente' },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 },
    )
  }

  return { pos, reale, stato, avvia }
}
