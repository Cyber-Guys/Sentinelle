export type Tema = 'scuro' | 'chiaro'

const CHIAVE = 'sentinelle-tema'
const COLORE_BARRA: Record<Tema, string> = { scuro: '#07090d', chiaro: '#f6f4ef' }

// Il tema e' gia' applicato a <html> dallo script inline in nuxt.config (niente lampo):
// qui si legge quello stato e lo si tiene allineato.
export function useTema() {
  const tema = useState<Tema>('tema', () =>
    import.meta.client && document.documentElement.dataset.tema === 'chiaro' ? 'chiaro' : 'scuro',
  )

  function imposta(t: Tema) {
    tema.value = t
    if (!import.meta.client) return
    document.documentElement.dataset.tema = t
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', COLORE_BARRA[t])
    try { localStorage.setItem(CHIAVE, t) } catch {}
  }

  const alterna = () => imposta(tema.value === 'scuro' ? 'chiaro' : 'scuro')
  return { tema, imposta, alterna }
}

// script eseguito in <head> prima del primo render
export const SCRIPT_TEMA = `(function(){var t='scuro';try{if(localStorage.getItem('${CHIAVE}')==='chiaro')t='chiaro'}catch(e){}document.documentElement.dataset.tema=t;})()`
