// Una sola EventSource condivisa (singleton di modulo): si apre al primo iscritto e si chiude quando non ce ne sono piu'.
type Fn = (dati: any) => void
const TIPI = ['segnalazione_nuova', 'segnalazione_aggiornata', 'segnalazione_valutata', 'mappatura_nuova', 'hotspot_aggiornati']
const iscritti = new Map<string, Set<Fn>>()
const stato = ref<'connesso' | 'riconnessione'>('riconnessione')
let es: EventSource | null = null

function apri() {
  es = new EventSource('/api/eventi')
  es.addEventListener('pronto', () => (stato.value = 'connesso'))
  es.onerror = () => (stato.value = 'riconnessione')
  for (const t of TIPI) {
    es.addEventListener(t, (e) => {
      stato.value = 'connesso'
      let d: any = {}
      try { d = JSON.parse((e as MessageEvent).data) } catch {}
      iscritti.get(t)?.forEach((f) => f(d))
    })
  }
}

export function useEventi() {
  function on(tipo: string, fn: Fn) {
    if (!iscritti.has(tipo)) iscritti.set(tipo, new Set())
    iscritti.get(tipo)!.add(fn)
    if (!es) apri()
    return () => {
      iscritti.get(tipo)?.delete(fn)
      if (![...iscritti.values()].some((s) => s.size)) { es?.close(); es = null; stato.value = 'riconnessione' }
    }
  }
  return { on, stato: readonly(stato) }
}
