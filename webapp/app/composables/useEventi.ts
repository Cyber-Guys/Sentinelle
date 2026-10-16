// Una sola EventSource condivisa (singleton di modulo) verso /api/eventi: si apre al primo iscritto,
// si chiude quando non ce ne sono piu'. Lo stesso canale usato dal cruscotto: le due app vedono gli stessi eventi.
type Fn = (dati: any) => void
const TIPI = ['segnalazione_nuova', 'segnalazione_aggiornata', 'segnalazione_valutata', 'hotspot_aggiornati']
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
      try { d = JSON.parse((e as MessageEvent).data) } catch { /* evento senza dati */ }
      iscritti.get(t)?.forEach((f) => f(d))
    })
  }
}

export function useEventi() {
  /** Iscrive `fn` agli eventi `tipi`; restituisce la funzione per disiscriversi. */
  function on(tipi: string | string[], fn: Fn) {
    const lista = Array.isArray(tipi) ? tipi : [tipi]
    for (const t of lista) {
      if (!iscritti.has(t)) iscritti.set(t, new Set())
      iscritti.get(t)!.add(fn)
    }
    if (!es) apri()
    return () => {
      for (const t of lista) iscritti.get(t)?.delete(fn)
      if (![...iscritti.values()].some((s) => s.size)) { es?.close(); es = null; stato.value = 'riconnessione' }
    }
  }
  return { on, stato: readonly(stato) }
}
