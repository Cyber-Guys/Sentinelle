// Un numero che conta verso il valore nuovo (~600 ms, easing in uscita). Istantaneo con reduced-motion.
export function useConteggio(sorgente: () => number, durata = 600) {
  const mostrato = ref(sorgente())
  let raf = 0
  watch(sorgente, (nuovo) => {
    cancelAnimationFrame(raf)
    const da = mostrato.value
    if (da === nuovo || window.matchMedia('(prefers-reduced-motion: reduce)').matches) { mostrato.value = nuovo; return }
    const t0 = performance.now()
    const passo = (t: number) => {
      const k = Math.min(1, (t - t0) / durata)
      mostrato.value = Math.round(da + (nuovo - da) * (1 - Math.pow(1 - k, 3)))
      if (k < 1) raf = requestAnimationFrame(passo)
    }
    raf = requestAnimationFrame(passo)
  })
  onBeforeUnmount(() => cancelAnimationFrame(raf))
  return mostrato
}
