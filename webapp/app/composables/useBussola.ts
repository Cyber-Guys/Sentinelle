// Direzione verso cui guarda l'utente (gradi dal nord). Sul telefono viene dal sensore; sul computer non c'e':
// per le prove ?dir=45 la fissa. Su iPhone il sensore chiede un permesso: va richiesto con un tocco (`richiedi`).
let attiva = false

export function useBussola() {
  const dir = useState<number | null>('bussola', () => null)
  const stato = useState<'spenta' | 'attiva' | 'negata' | 'assente'>('bussola-stato', () => 'spenta')
  const serveTocco = useState('bussola-tocco', () => false)

  function gestore(e: DeviceOrientationEvent & { webkitCompassHeading?: number }) {
    let g: number | null = null
    if (typeof e.webkitCompassHeading === 'number') g = e.webkitCompassHeading
    else if (e.absolute && typeof e.alpha === 'number') g = (360 - e.alpha) % 360
    if (g === null || Number.isNaN(g)) return
    // media circolare: toglie il tremolio del sensore
    const prima = dir.value
    dir.value = prima === null ? g : (prima + ((((g - prima + 540) % 360) - 180) * 0.25) + 360) % 360
    stato.value = 'attiva'
  }

  function ascolta() {
    if (attiva) return
    attiva = true
    window.addEventListener('deviceorientationabsolute', gestore as EventListener, true)
    window.addEventListener('deviceorientation', gestore as EventListener, true)
    setTimeout(() => { if (dir.value === null) stato.value = 'assente' }, 2500)
  }

  function avvia() {
    if (!import.meta.client) return
    const forzata = Number(new URLSearchParams(location.search).get('dir'))
    if (new URLSearchParams(location.search).has('dir') && Number.isFinite(forzata)) {
      dir.value = ((forzata % 360) + 360) % 360
      stato.value = 'attiva'
      return
    }
    const E = window.DeviceOrientationEvent as unknown as { requestPermission?: () => Promise<string> } | undefined
    if (!E) { stato.value = 'assente'; return }
    if (typeof E.requestPermission === 'function') { serveTocco.value = true; return } // iPhone
    ascolta()
  }

  async function richiedi() {
    const E = window.DeviceOrientationEvent as unknown as { requestPermission?: () => Promise<string> } | undefined
    try {
      if (typeof E?.requestPermission === 'function') {
        if ((await E.requestPermission()) !== 'granted') { stato.value = 'negata'; return }
      }
      serveTocco.value = false
      ascolta()
    } catch {
      stato.value = 'negata'
    }
  }

  return { dir, stato, serveTocco, avvia, richiedi }
}
