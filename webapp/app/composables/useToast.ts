export interface Messaggio { id: number; testo: string; errore: boolean }
let n = 0

export function useToast() {
  const messaggi = useState<Messaggio[]>('toast', () => [])
  function mostra(testo: string, errore = false) {
    const m = { id: ++n, testo, errore }
    messaggi.value = [...messaggi.value.slice(-2), m]
    setTimeout(() => (messaggi.value = messaggi.value.filter((x) => x.id !== m.id)), errore ? 5000 : 2800)
  }
  return { messaggi, ok: (t: string) => mostra(t), errore: (t: string) => mostra(t, true) }
}
