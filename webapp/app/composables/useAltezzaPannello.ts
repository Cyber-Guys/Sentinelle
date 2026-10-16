// Pannello che sale dal basso con la maniglia in alto al centro: l'altezza si regola trascinando la maniglia
// (dito o mouse), su allarga e giu' restringe. Se `chiudi` e' dato, trascinare ben sotto il minimo lo chiude.
// Un tocco sulla maniglia alterna tra altezza naturale e massima; da tastiera, frecce su e giu'.
export function useAltezzaPannello(o: { min?: number; max?: () => number; chiudi?: () => void; fine?: () => void } = {}) {
  const min = o.min ?? 150
  const altezza = ref<number | null>(null) // px; null = quanto serve al contenuto
  const scende = ref<number | 'fuori'>(0) // quanto il dito e' sceso oltre il minimo: il pannello lo segue
  const max = () => Math.round(o.max?.() ?? window.innerHeight * 0.92)
  const limita = (h: number) => Math.round(Math.min(max(), Math.max(min, h)))
  const pannello = (e: Event) => (e.currentTarget as HTMLElement).closest<HTMLElement>('.foglio')
  let presa: { y: number; h: number; mosso: boolean; grezza: number } | null = null

  function giu(e: PointerEvent) {
    const p = pannello(e)
    if (!p) return
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
    presa = { y: e.clientY, h: p.offsetHeight, mosso: false, grezza: p.offsetHeight }
  }

  function muovi(e: PointerEvent) {
    if (!presa) return
    const dy = e.clientY - presa.y
    if (!presa.mosso && Math.abs(dy) < 5) return
    presa.mosso = true
    presa.grezza = presa.h - dy
    altezza.value = limita(presa.grezza)
    scende.value = o.chiudi ? Math.max(0, Math.round(min - presa.grezza)) : 0
  }

  function su() {
    const p = presa
    presa = null
    if (!p) return
    if (!p.mosso) { altezza.value = altezza.value === null ? max() : null; o.fine?.(); return }
    if (o.chiudi && p.grezza < min - 60) {
      scende.value = 'fuori'
      setTimeout(o.chiudi, 200)
      return
    }
    scende.value = 0
    o.fine?.()
  }

  function tasto(e: KeyboardEvent) {
    const verso = e.key === 'ArrowUp' ? 1 : e.key === 'ArrowDown' ? -1 : 0
    if (verso) altezza.value = limita((altezza.value ?? pannello(e)?.offsetHeight ?? min) + verso * 48)
    else if (e.key === 'Enter' || e.key === ' ') altezza.value = altezza.value === null ? max() : null
    else return
    e.preventDefault()
    o.fine?.()
  }

  const stile = computed(() => ({
    ...(altezza.value !== null && { height: `${altezza.value}px` }),
    ...(scende.value === 'fuori'
      ? { translate: '0 100%', transition: 'translate 0.2s var(--ease-uscita)' }
      : scende.value ? { translate: `0 ${scende.value}px` } : {}),
  }))

  const reset = () => { altezza.value = null; scende.value = 0 }
  const maniglia = { onPointerdown: giu, onPointermove: muovi, onPointerup: su, onPointercancel: su, onKeydown: tasto }

  return { stile, maniglia, reset }
}
