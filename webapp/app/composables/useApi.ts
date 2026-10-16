// Tutte le chiamate al backend passano da /api (nginx in produzione, Nitro in nuxt dev): stessa origine, niente CORS.
export function useApi() {
  const base = useRuntimeConfig().public.apiBaseUrl as string
  return <T>(percorso: string, opzioni: Parameters<typeof $fetch>[1] = {}) => $fetch<T>(base + percorso, opzioni) as Promise<T>
}

export function urlMedia(percorso: string | null | undefined): string | undefined {
  return percorso ? (useRuntimeConfig().public.apiBaseUrl as string) + percorso : undefined
}

// Frase non tecnica per l'errore di una chiamata: mai il messaggio grezzo a schermo.
export function messaggioErrore(e: unknown): string {
  const err = e as { statusCode?: number; data?: { detail?: unknown } }
  const detail = err?.data?.detail
  if (typeof detail === 'string' && detail.length < 120) return detail
  if (!err?.statusCode) return 'Non riesco a collegarmi. Controlla la connessione e riprova.'
  if (err.statusCode === 404) return 'Non trovo quello che cerchi.'
  if (err.statusCode === 413) return 'Il file è troppo grande. Prova con un video più corto.'
  if (err.statusCode >= 500) return 'Qualcosa non ha funzionato da parte nostra. Riprova tra poco.'
  return 'Non è andata a buon fine. Riprova.'
}
