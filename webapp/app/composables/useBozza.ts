// Bozza della segnalazione, condivisa tra la Mappa (dove si scatta la foto) e Segnala.
// I File stanno in shallowRef: un proxy reattivo non e' piu' un Blob e FormData lo rifiuterebbe.
const foto = shallowRef<File | null>(null)
const video = shallowRef<File | null>(null)
const nota = ref('')
const tipo = ref<TipoSegnalazione | null>(null)
const punto = ref<{ lat: number; lon: number } | null>(null) // posizione scelta a mano; null = quella del telefono

export function useBozza() {
  function azzera() {
    foto.value = null
    video.value = null
    nota.value = ''
    tipo.value = null
    punto.value = null
  }
  return { foto, video, nota, tipo, punto, azzera }
}
