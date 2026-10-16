// Identita' senza password (demo): l'id dell'utente sta in localStorage. Vedi la specifica, sezione "Identita'".
const CHIAVE = 'sentinelle.utente'

function leggi(): number | null {
  try {
    const v = Number(localStorage.getItem(CHIAVE))
    return Number.isInteger(v) && v > 0 ? v : null
  } catch {
    return null
  }
}

export function useSessione() {
  const api = useApi()
  const id = useState<number | null>('sessione-id', () => (import.meta.client ? leggi() : null))
  const utente = useState<Utente | null>('sessione-utente', () => null)

  async function carica() {
    if (!id.value) return
    try {
      utente.value = await api<Utente>(`/utenti/${id.value}`)
    } catch (e) {
      if ((e as { statusCode?: number }).statusCode === 404) esci()
    }
  }

  function entra(u: Utente) {
    id.value = u.id
    utente.value = u
    try { localStorage.setItem(CHIAVE, String(u.id)) } catch { /* modalita' privata: vale solo per questa visita */ }
  }

  function esci() {
    id.value = null
    utente.value = null
    try { localStorage.removeItem(CHIAVE) } catch { /* niente */ }
  }

  return { id, utente, carica, entra, esci }
}
