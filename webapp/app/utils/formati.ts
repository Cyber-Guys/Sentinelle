// Testi per le persone: date, distanze, direzioni

export function fa(iso: string | null): string {
  if (!iso) return ''
  const min = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  if (min < 1) return 'ora'
  if (min < 90) return `${min} min fa`
  const ore = Math.round(min / 60)
  if (ore < 36) return `${ore} h fa`
  return `${Math.round(ore / 24)} giorni fa`
}

const MESI = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']

export function dataBreve(iso: string): string {
  const d = new Date(iso)
  const ora = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  return `${d.getDate()} ${MESI[d.getMonth()]}, ${ora}`
}

export function km(n: number | null | undefined): string {
  if (n == null) return ''
  return `${n.toFixed(n < 10 ? 1 : 0).replace('.', ',')} km`
}

// "vicino a Casa" oppure "2,3 km da Casa"
export function daCasa(n: number | null | undefined, nome: string | null | undefined): string {
  if (n == null || !nome) return ''
  return n < 0.15 ? `vicino a ${nome}` : `${km(n)} da ${nome}`
}

export function distanzaTesto(m: number): string {
  return m < 950 ? `${Math.round(m / 10) * 10} m` : km(m / 1000)
}

const PUNTI = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ovest', 'ovest', 'nord-ovest']
export function puntoCardinale(gradi: number): string {
  return PUNTI[Math.round((((gradi % 360) + 360) % 360) / 45) % 8]!
}

// distanza in metri tra due punti (haversine)
export function metri(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const p = Math.PI / 180
  const x = Math.sin(((b.lat - a.lat) * p) / 2) ** 2 + Math.cos(a.lat * p) * Math.cos(b.lat * p) * Math.sin(((b.lon - a.lon) * p) / 2) ** 2
  return 12742000 * Math.asin(Math.sqrt(x))
}

export function iniziale(nome: string | undefined): string {
  return (nome ?? '?').trim().charAt(0).toUpperCase() || '?'
}

// al plurale giusto: 1 zona, 2 zone
export function plurale(n: number, uno: string, molti: string): string {
  return `${n} ${n === 1 ? uno : molti}`
}

// riduce una foto prima dell'invio: i telefoni fanno foto da 5-10 MB, il backend non ne ha bisogno
export async function ridimensiona(file: File, lato = 1600): Promise<File> {
  if (!file.type.startsWith('image/') || file.type === 'image/gif') return file
  try {
    const bmp = await createImageBitmap(file)
    const s = Math.min(1, lato / Math.max(bmp.width, bmp.height))
    if (s === 1 && file.size < 1_500_000) return file
    const c = document.createElement('canvas')
    c.width = Math.round(bmp.width * s)
    c.height = Math.round(bmp.height * s)
    c.getContext('2d')!.drawImage(bmp, 0, 0, c.width, c.height)
    const blob = await new Promise<Blob | null>((ok) => c.toBlob(ok, 'image/jpeg', 0.85))
    return blob ? new File([blob], file.name.replace(/\.\w+$/, '') + '.jpg', { type: 'image/jpeg' }) : file
  } catch {
    return file
  }
}
