// Avvisi per le localita' dell'utente, con priorita'. Si aggiornano ogni 30 s e a ogni evento live del backend
// (stesso canale SSE del cruscotto). Un avviso nuovo urgente o importante compare come messaggio e, se il
// browser lo permette, come notifica del sistema. Notifiche a app chiusa: fuori da questa consegna.
const INTERVALLO_MS = 30000
const CHIAVE_VISTI = 'sentinelle.avvisi-visti'

let timer: ReturnType<typeof setInterval> | null = null
let disiscrivi: (() => void) | null = null
let rinvio: ReturnType<typeof setTimeout> | null = null
const visti = new Set<string>()
let primoCaricamento = true

function leggiVisti() {
  try { for (const i of JSON.parse(sessionStorage.getItem(CHIAVE_VISTI) ?? '[]')) visti.add(i) } catch { /* niente */ }
}
function salvaVisti() {
  try { sessionStorage.setItem(CHIAVE_VISTI, JSON.stringify([...visti].slice(-200))) } catch { /* niente */ }
}

export function useAvvisi() {
  const api = useApi()
  const { id } = useSessione()
  const { on } = useEventi()
  const toast = useToast()
  const lista = useState<Avviso[]>('avvisi', () => [])
  const caricato = useState('avvisi-caricato', () => false)
  const permesso = useState<NotificationPermission | 'non-supportato'>('avvisi-permesso', () => 'default')

  function leggiPermesso() {
    permesso.value = import.meta.client && 'Notification' in window ? Notification.permission : 'non-supportato'
  }

  function segnala(a: Avviso) {
    toast.mostra(`${PRIORITA[a.priorita].nome}: ${a.titolo}`, a.priorita === 'urgente')
    try { if (a.priorita === 'urgente') navigator.vibrate?.([200, 100, 200]) } catch { /* niente */ }
    try {
      if ('Notification' in window && Notification.permission === 'granted' && document.hidden) {
        new Notification(`${PRIORITA[a.priorita].nome}: ${a.titolo}`, { body: a.testo, icon: '/icona.svg', tag: a.id })
      }
    } catch { /* su alcuni telefoni serve un service worker: l'avviso resta in app */ }
  }

  async function aggiorna() {
    if (!id.value) return
    try {
      const nuovi = await api<Avviso[]>(`/utenti/${id.value}/avvisi`)
      if (primoCaricamento) { leggiVisti(); primoCaricamento = false; nuovi.forEach((a) => visti.add(a.id)) }
      for (const a of nuovi) {
        if (!visti.has(a.id)) {
          visti.add(a.id)
          if (a.priorita !== 'informazione') segnala(a)
        }
      }
      salvaVisti()
      lista.value = nuovi
    } catch { /* si tengono gli ultimi avvisi: a rete assente non si svuota lo schermo */ }
    caricato.value = true
  }

  function avvia() {
    leggiPermesso()
    if (timer) return
    aggiorna()
    timer = setInterval(aggiorna, INTERVALLO_MS)
    disiscrivi = on(['segnalazione_nuova', 'segnalazione_aggiornata', 'segnalazione_valutata'], () => {
      if (rinvio) clearTimeout(rinvio)
      rinvio = setTimeout(aggiorna, 600)
    })
  }

  function ferma() {
    if (timer) clearInterval(timer)
    timer = null
    disiscrivi?.()
    disiscrivi = null
    lista.value = []
    caricato.value = false
    primoCaricamento = true
    visti.clear()
  }

  async function richiediPermesso() {
    if (!('Notification' in window)) return
    await Notification.requestPermission()
    leggiPermesso()
  }

  const urgenti = computed(() => lista.value.filter((a) => a.priorita === 'urgente').length)

  return { lista, caricato, permesso, urgenti, aggiorna, avvia, ferma, richiediPermesso, leggiPermesso }
}
