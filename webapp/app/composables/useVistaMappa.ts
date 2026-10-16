// Vista della mappa: satellite (default) oppure mappa normale. La scelta resta salvata nel telefono.
// Il satellite viene da internet: senza rete si parte direttamente dalla mappa normale (che e' tutta locale).
import type { Vista } from '~/utils/mappa'

const CHIAVE = 'sentinelle.vista-mappa'

function iniziale(): Vista {
  try {
    const v = localStorage.getItem(CHIAVE)
    if (v === 'mappa' || v === 'satellite') return v
  } catch { /* niente */ }
  return import.meta.client && navigator.onLine === false ? 'mappa' : 'satellite'
}

export function useVistaMappa() {
  const vista = useState<Vista>('vista-mappa', iniziale)
  function imposta(v: Vista, salva = true) {
    vista.value = v
    if (!salva) return
    try { localStorage.setItem(CHIAVE, v) } catch { /* niente */ }
  }
  return { vista, imposta }
}
