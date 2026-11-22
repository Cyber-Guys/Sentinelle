// Cattura le schermate reali per il trailer dallo stack Docker in esecuzione: app cittadino su :3000, dashboard COP
// su :3001. Dati: quelli demo gia' nel database (gruppo Settimo San Pietro). Gli stati di passaggio (invio,
// certificazione, soccorritori allertati, mezzi sul posto) si ottengono intercettando le risposte API in questo
// browser: nel database non si scrive niente. Uscita: schermate/*.png|jpg e schermate/meta.js (rettangoli e
// posizioni usati dalle animazioni di trailer.html). Uso: node cattura.mjs
import { chromium } from 'playwright'
import { mkdir, readFile, writeFile } from 'node:fs/promises'

const QUI = new URL('.', import.meta.url).pathname
const OUT = `${QUI}schermate`
const APP = 'http://localhost:3000'
const DASH = 'http://localhost:3001'
const FOTO = `${QUI}../../../dati/demo_foto/fiamme-1.jpg`
const BACKEND = 'http://localhost:8000'
const IO = { lat: 39.2915, lon: 9.1935 } // il cittadino, 300 m a sud di casa, guarda verso nord
const DIR = 10
const AVVISATI = 20 // conteggio reale (cop.avvisati) per il gruppo, letto in sola lettura dal database
// gli id cambiano a ogni semina_cop.py: profilo "Sentinella 3 (demo-cop)" (Casa a 39.2942, 9.1928, 0,9 km a sud
// dell'incendio di Settimo San Pietro) e la sua segnalazione di fuoco con 7 conferme
const UTENTE = (await (await fetch(`${BACKEND}/utenti`)).json()).find((u) => u.nome === 'Sentinella 3 (demo-cop)')?.id
const ATTIVE = await (await fetch(`${BACKEND}/segnalazioni/attive`)).json()
const BERSAGLIO = ATTIVE.find((s) => s.tipo === 'fuoco' && s.conferme === 7 && Math.abs(s.lat - 39.3018) < 0.002)?.id
if (!UTENTE || !BERSAGLIO) throw new Error('dati demo mancanti: lanciare scripts/semina_cop.py')
console.log('utente', UTENTE, 'segnalazione', BERSAGLIO)
const TEL = { w: 393, h: 793, dpr: 3, barra: 59, sotto: 34 } // iPhone 15 Pro: 852 punti meno la barra di stato

// node cattura.mjs [segnala] [mappa] [viaggio] [dashboard]: senza argomenti tutte le sezioni; le altre restano in meta.js
const SEZIONI = process.argv.slice(2)
const vuoi = (s) => !SEZIONI.length || SEZIONI.includes(s)
const precedente = await readFile(`${OUT}/meta.js`, 'utf8').then((t) => JSON.parse(t.slice(t.indexOf('{')))).catch(() => ({}))
const META = { ...precedente, creato: new Date().toISOString(), telefono: TEL, io: IO, dir: DIR, bersaglio: BERSAGLIO }
// posizioni vere (per proiettare Casa e calibrare lo zoom) e ora della cattura per la barra di stato del telefono
META.segnalazioni = ATTIVE.map(({ id, tipo, lat, lon, conferme }) => ({ id, tipo, lat, lon, conferme }))
META.casa = (await (await fetch(`${BACKEND}/utenti/${UTENTE}/localita`)).json()).map(({ nome, lat, lon }) => ({ nome, lat, lon }))[0]
const r1 = (v) => Math.round(v * 10) / 10
const box = async (loc) => {
  const b = await loc.first().boundingBox({ timeout: 3000 }).catch(() => null)
  return b && { x: r1(b.x), y: r1(b.y), w: r1(b.width), h: r1(b.height) }
}
const attendi = (p, ms) => p.waitForTimeout(ms)

async function attendiMappa(p, extra = 2500) {
  await p.waitForSelector('.maplibregl-canvas', { timeout: 30000 })
  await p.waitForLoadState('networkidle').catch(() => {})
  await attendi(p, extra)
  await p.waitForLoadState('networkidle').catch(() => {})
}

// pin HTML della mappa dell'app: posizione sullo schermo (px CSS), tipo, conteggio del gruppo, etichetta
async function marcatori(p) {
  return p.evaluate(() => [...document.querySelectorAll('.maplibregl-marker')].map((m) => {
    const pin = m.querySelector('.pin'), io = m.querySelector('.io-punto')
    const el = pin ?? io ?? m
    const b = el.getBoundingClientRect()
    return {
      x: Math.round((b.left + b.width / 2) * 10) / 10, y: Math.round((b.top + b.height / 2) * 10) / 10,
      classi: pin ? pin.className : io ? 'io' : m.className,
      conteggio: m.querySelector('.pin-conteggio')?.textContent?.trim() || null,
      etichetta: m.querySelector('.pin-etichetta')?.textContent?.trim() || null,
      nome: m.getAttribute('aria-label') || pin?.getAttribute('aria-label') || m.title || null,
    }
  }))
}

// risposte API riscritte: elenco vuoto ("prima" della segnalazione), invio, stato ufficiale della segnalazione
function intercetta(p, stato) {
  return p.route(/\/api\//, async (route) => {
    const req = route.request()
    const u = new URL(req.url())
    if (u.pathname.endsWith('/eventi')) return route.abort() // niente eventi live: catture ripetibili
    if (stato.vuoto && (u.pathname.endsWith('/segnalazioni/attive') || /\/utenti\/\d+\/avvisi$/.test(u.pathname))) {
      return route.fulfill({ json: [] })
    }
    if (req.method() === 'POST' && u.pathname.endsWith('/api/segnalazioni')) {
      return route.fulfill({ json: {
        id: 9001, tipo: 'fuoco', lat: IO.lat, lon: IO.lon, direzione: DIR, nota: 'Fiamme sulla collina', stato: 'in_attesa',
        stato_ufficiale: 'in_verifica', priorita: 63, foto_url: null, video_url: null, creata_il: new Date().toISOString(),
        fattori: [], motivazioni: [],
      } })
    }
    if (req.method() !== 'GET') return route.abort() // qualunque altra scrittura resta fuori dal database
    if (stato.ritocca && u.pathname.endsWith('/segnalazioni/attive')) {
      // questo profilo demo ha gia' confermato: la scheda si mostra come la vede un vicino che non ha ancora risposto
      const r = await route.fetch()
      const j = await r.json()
      for (const s of j) {
        if (s.id !== BERSAGLIO) continue
        Object.assign(s, { mio_voto: null, mia: false })
        if (stato.ufficiale) s.stato_ufficiale = stato.ufficiale
      }
      return route.fulfill({ response: r, json: j })
    }
    return route.continue()
  })
}

async function telefono(browser, stato) {
  const ctx = await browser.newContext({
    serviceWorkers: 'block', // un service worker scavalca page.route: le risposte finte non arriverebbero
    viewport: { width: TEL.w, height: TEL.h }, deviceScaleFactor: TEL.dpr, isMobile: true, hasTouch: true,
    geolocation: { latitude: IO.lat, longitude: IO.lon, accuracy: 8 }, permissions: ['geolocation'],
    locale: 'it-IT', timezoneId: 'Europe/Rome',
  })
  await ctx.addInitScript((id) => {
    localStorage.setItem('sentinelle.utente', String(id))
    localStorage.setItem('sentinelle.vista-mappa', 'satellite')
  }, UTENTE)
  const p = await ctx.newPage()
  p.on('pageerror', (e) => console.log('  [errore pagina]', e.message))
  const cdp = await ctx.newCDPSession(p)
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 0, bottom: TEL.sotto, left: 0, right: 0 } })
  await intercetta(p, stato)
  return { ctx, p }
}

const foto = (p, nome, opz = {}) => p.screenshot({ path: `${OUT}/${nome}`, ...opz })

async function chiudiFoglio(p) {
  await p.keyboard.press('Escape')
  await attendi(p, 500)
  if (await p.locator('.velo').count()) { await p.mouse.click(TEL.w / 2, 12); await attendi(p, 600) }
}

// apre la scheda della segnalazione bersaglio (7 conferme) toccando i pin; i gruppi si sciolgono avvicinandosi
async function apriScheda(p) {
  for (let giro = 0; giro < 4; giro++) {
    const pin = (await marcatori(p)).filter((m) => m.classi.includes('pin-fuoco') || m.classi.includes('pin-fumo'))
    for (const m of pin.filter((x) => !x.conteggio)) {
      await p.mouse.click(m.x, m.y)
      await attendi(p, 900)
      const testo = (await p.locator('.velo').first().textContent().catch(() => '')) || ''
      if (testo.includes('7 conferme')) return true
      if (testo.includes('Apri')) { // elenco di un gruppo nello stesso punto
        const n = await p.getByRole('button', { name: 'Apri' }).count()
        for (let i = 0; i < n; i++) {
          await p.getByRole('button', { name: 'Apri' }).nth(i).click()
          await attendi(p, 700)
          if (((await p.locator('.velo').first().textContent()) || '').includes('7 conferme')) return true
        }
      }
      await chiudiFoglio(p)
    }
    const gruppo = pin.find((x) => x.conteggio)
    if (!gruppo) break
    await p.mouse.click(gruppo.x, gruppo.y)
    await attendiMappa(p, 1800)
  }
  return false
}

async function rettScheda(p) {
  return {
    foglio: await box(p.locator('.velo .foglio')),
    stato: await box(p.locator('.velo .foglio .etichetta')),
    conferme: await box(p.locator('.velo .foglio .etichetta').nth(1)),
    vedo: await box(p.getByRole('button', { name: /Lo vedo anch/ })),
  }
}

// ---------------------------------------------------------------------------------------------------------------
await mkdir(OUT, { recursive: true })
const browser = await chromium.launch()

// A1-A4: il cittadino vede il fuoco e lo segnala (prima: nessuna segnalazione vicina)
if (vuoi('segnala')) {
  console.log('A1-A4 segnalazione')
  META.ora = new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Rome' })
  const stato = { vuoto: true }
  const { ctx, p } = await telefono(browser, stato)
  await p.goto(`${APP}/?dir=${DIR}`, { waitUntil: 'domcontentloaded' })
  await attendiMappa(p, 2000)
  await p.getByRole('button', { name: 'Torna alla mia posizione' }).click()
  await attendiMappa(p, 2500)
  await foto(p, 'a1-mappa.png')
  META.a1 = {
    segnala: await box(p.locator('label.gigante')), banner: await box(p.locator('.banner')),
    marcatori: await marcatori(p),
  }

  const [scelta] = await Promise.all([p.waitForEvent('filechooser'), p.locator('label.gigante').click()])
  await scelta.setFiles(FOTO)
  await p.waitForURL(/\/segnala/)
  await p.waitForFunction(() => [...document.images].some((i) => i.src.startsWith('blob:') && i.complete && i.naturalWidth > 0))
  await attendi(p, 1200)
  await foto(p, 'a2-segnala.png')
  META.a2 = {
    foto: await box(p.locator('img[src^="blob:"]')), tessere: await Promise.all([0, 1, 2].map((i) => box(p.locator('.tessera').nth(i)))),
    nota: await box(p.locator('.campo').filter({ has: p.locator('textarea') })), testo: await box(p.locator('textarea')),
    microfono: await box(p.locator('.campo button')), invia: await box(p.locator('.gigante').last()),
  }
  await p.locator('.tessera').first().click()
  await attendi(p, 600)
  await foto(p, 'a3a-tipo.png')
  await p.locator('textarea').fill('Fiamme sulla collina')
  await p.locator('textarea').blur()
  await attendi(p, 500)
  await foto(p, 'a3b-nota.png')
  META.a3 = { invia: await box(p.locator('.gigante').last()), testo: await box(p.locator('textarea')) }

  await p.locator('.gigante').last().click()
  await p.getByText('Segnalazione inviata').waitFor()
  await attendi(p, 900)
  await foto(p, 'a4-inviata.png')
  META.a4 = { scheda: await box(p.locator('.scheda').first()), icona: await box(p.locator('.scheda .tile-tipo')), titolo: await box(p.getByText('Segnalazione inviata')) }
  await ctx.close()
}

// A5-A7 e mappe D: la mappa vera con il gruppo di Settimo San Pietro, la scheda negli stati ufficiali, gli avvisi
if (vuoi('mappa')) {
  console.log('A5-A7 e zoom D')
  const stato = { vuoto: false, ritocca: true, ufficiale: null }
  const { ctx, p } = await telefono(browser, stato)
  await p.goto(`${APP}/?dir=${DIR}`, { waitUntil: 'domcontentloaded' })
  await attendiMappa(p, 3000)
  await foto(p, 'a6-mappa.png')
  META.a6 = { banner: await box(p.locator('.banner')), marcatori: await marcatori(p) }

  META.a5 = {}
  for (const [nome, uff] of [['verifica', null], ['allertati', 'allertati'], ['mezzi', 'mezzi_sul_posto']]) {
    stato.ufficiale = uff
    if (uff) { await p.reload({ waitUntil: 'domcontentloaded' }); await attendiMappa(p, 3000) }
    if (!(await apriScheda(p))) throw new Error('scheda della segnalazione bersaglio non trovata')
    await attendi(p, 700)
    await foto(p, `a5-${nome}.png`)
    META.a5[nome] = await rettScheda(p)
  }
  await chiudiFoglio(p)
  await attendi(p, 800)
  await foto(p, 'a6-dopo.png')
  META.d = { banner: await box(p.locator('.banner')), mappa: await box(p.locator('.maplibregl-canvas')), livelli: [] }

  // livelli dello zoom indietro: stessa vista, un livello in meno a ogni passo (tastiera di MapLibre)
  for (let k = 0; k < 4; k++) {
    if (k > 0) {
      await p.locator('.maplibregl-canvas').focus()
      await p.keyboard.press('Minus')
      await attendiMappa(p, 2200)
    }
    const livello = { marcatori: await marcatori(p) }
    if (k === 0) {
      const ui = await p.addStyleTag({ content: `
        .maplibregl-canvas, .maplibregl-marker, .maplibregl-control-container { visibility: hidden !important; }
        html, body, #__nuxt, .telefono, .schermata, .mappa-contenitore, .maplibregl-map { background: transparent !important; }` })
      await foto(p, 'd-ui.png', { omitBackground: true })
      await ui.evaluate((s) => s.remove())
    }
    const solo = await p.addStyleTag({ content: '* { visibility: hidden !important; } .maplibregl-canvas { visibility: visible !important; }' })
    const c = META.d.mappa
    await foto(p, `d-mappa-${k}.jpg`, { type: 'jpeg', quality: 90, clip: { x: c.x, y: c.y, width: c.w, height: c.h } })
    await solo.evaluate((s) => s.remove())
    META.d.livelli.push(livello)
    console.log('  livello', k, livello.marcatori.length, 'pin')
  }

  await p.reload({ waitUntil: 'domcontentloaded' })
  await attendiMappa(p, 3000)
  await p.locator('.banner').click()
  await p.getByText('Vicino a te').waitFor()
  await attendi(p, 900)
  await foto(p, 'a7-avvisi.png')
  const righe = p.locator('.velo .riga')
  META.a7 = { foglio: await box(p.locator('.velo .foglio')), righe: [] }
  for (let i = 0; i < Math.min(await righe.count(), 6); i++) META.a7.righe.push(await box(righe.nth(i)))
  await ctx.close()
}

// B: mappa satellitare grande (la stessa dell'app, a tutto schermo) per il viaggio della segnalazione
if (vuoi('viaggio')) {
  console.log('B mappa grande')
  const ctx = await browser.newContext({
    serviceWorkers: 'block', viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, locale: 'it-IT', timezoneId: 'Europe/Rome',
    geolocation: { latitude: IO.lat, longitude: IO.lon, accuracy: 8 }, permissions: ['geolocation'],
  })
  await ctx.addInitScript((id) => {
    localStorage.setItem('sentinelle.utente', String(id))
    localStorage.setItem('sentinelle.vista-mappa', 'satellite')
    document.addEventListener('DOMContentLoaded', () => {
      const s = document.createElement('style')
      s.textContent = '.schermata > .relative:first-child { position: fixed !important; inset: 0 !important; z-index: 50; }'
      document.head.appendChild(s)
    })
  }, UTENTE)
  const p = await ctx.newPage()
  await intercetta(p, { vuoto: true })
  await p.goto(`${APP}/?dir=${DIR}`, { waitUntil: 'domcontentloaded' })
  await attendiMappa(p, 2000)
  await p.getByRole('button', { name: 'Torna alla mia posizione' }).click()
  await attendiMappa(p, 3000)
  META.b = { mappa: await box(p.locator('.maplibregl-canvas')), livelli: [] }
  for (let k = 0; k < 6; k++) { // zoom 16 -> 11: l'ultimo livello copre Cagliari con margine
    if (k > 0) {
      await p.locator('.maplibregl-canvas').focus()
      await p.keyboard.press('Minus')
      await attendiMappa(p, 2500)
    }
    const io = (await marcatori(p)).find((m) => m.classi === 'io')
    const solo = await p.addStyleTag({ content: '* { visibility: hidden !important; } .maplibregl-canvas { visibility: visible !important; }' })
    const c = META.b.mappa
    await foto(p, `b-mappa-${k}.jpg`, { type: 'jpeg', quality: 88, clip: { x: c.x, y: c.y, width: c.w, height: c.h } })
    await solo.evaluate((s) => s.remove())
    META.b.livelli.push({ io })
    console.log('  livello', k, 'io', io && `${io.x},${io.y}`)
  }
  await ctx.close()
}

// C: dashboard COP (font di sistema sostituito da Inter: in headless Linux sarebbe DejaVu)
if (vuoi('dashboard')) {
  console.log('C dashboard')
  const inter = (await readFile(`${QUI}fonts/Inter-Variable.woff2`)).toString('base64')
  const css = `@font-face { font-family: 'Inter'; src: url(data:font/woff2;base64,${inter}) format('woff2'); font-weight: 100 900; font-style: normal; }
    :root { --font-sans: 'Inter', system-ui, sans-serif !important; --font-display: 'Inter', system-ui, sans-serif !important; }
    html, body { font-family: 'Inter', system-ui, sans-serif !important; }`
  const ctx = await browser.newContext({
    serviceWorkers: 'block', viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, locale: 'it-IT', timezoneId: 'Europe/Rome',
  })
  await ctx.addInitScript((c) => document.addEventListener('DOMContentLoaded', () => {
    const s = document.createElement('style'); s.textContent = c; document.head.appendChild(s)
  }), css)
  const p = await ctx.newPage()
  p.on('pageerror', (e) => console.log('  [errore pagina]', e.message))
  await p.route(/\/api\//, (route) => {
    const req = route.request()
    const u = new URL(req.url())
    if (u.pathname.endsWith('/eventi')) return route.abort()
    // certificare un gruppo = certifica del capo + conferma degli altri membri: tutte risposte finte
    if (req.method() === 'POST' && /\/cop\/segnalazioni\/\d+\/certifica$/.test(u.pathname)) return route.fulfill({ json: { avvisati: AVVISATI } })
    const conferma = req.method() === 'POST' && u.pathname.match(/\/segnalazioni\/(\d+)\/conferma$/)
    if (conferma) return route.fulfill({ json: { id: Number(conferma[1]), stato: 'confermata', stato_ufficiale: 'allertati' } })
    if (req.method() !== 'GET') return route.abort()
    return route.continue()
  })
  await p.goto(`${DASH}/dashboard?area=cagliari`, { waitUntil: 'domcontentloaded' })
  await p.evaluate(() => document.fonts.ready)
  await attendiMappa(p, 4000)
  await foto(p, 'd1-area.jpg', { type: 'jpeg', quality: 93 })
  // contatore della scheda Segnalazioni: rettangolo e stile, per farlo salire da 2 a 3 all'arrivo della segnalazione
  const badge = p.getByRole('button', { name: /Segnalazioni/ }).locator('span').last()
  META.d1 = {
    schedaSegnalazioni: await box(p.getByRole('button', { name: /Segnalazioni/ })), badge: await box(badge),
    badgeStile: await badge.evaluate((el) => { const c = getComputedStyle(el); return { bg: c.backgroundColor, col: c.color, fs: c.fontSize, fw: c.fontWeight, r: c.borderRadius } }),
  }

  await p.goto(`${DASH}/dashboard?area=cagliari&vista=segnalazioni`, { waitUntil: 'domcontentloaded' })
  await p.getByText('Certifica incendio').waitFor()
  await p.waitForFunction(() => [...document.querySelectorAll('.foto img')].every((i) => i.complete && i.naturalWidth > 0))
  await p.evaluate(() => document.fonts.ready)
  await attendi(p, 1500)
  await foto(p, 'd2-segnalazioni.jpg', { type: 'jpeg', quality: 93 })
  const coda = p.locator('li button').filter({ hasText: /segnalazion/ })
  META.d2 = {
    coda: await Promise.all([0, 1, 2].map((i) => box(coda.nth(i)))),
    codaNomi: await coda.allTextContents(),
    titoloCoda: await box(p.getByText('Da verificare').first()),
    foto: await box(p.locator('.foto').first()),
    conferme: await box(p.getByText('Conferme dai vicini').locator('xpath=ancestor::*[self::li or self::div][1]')),
    priorita: await box(p.getByText('Priorità calcolata').locator('xpath=..')),
    certifica: await box(p.getByRole('button', { name: /Certifica incendio/ })),
  }
  // capo del gruppo (centro del volo della mappa), dall'intestazione della scheda
  const [capoLat, capoLon] = ((await p.locator('#t-foto + p').textContent()) || '').match(/(\d+\.\d+),\s*(\d+\.\d+)/).slice(1).map(Number)
  await p.getByRole('button', { name: /Certifica incendio/ }).click()
  await p.getByText(/Incendio certificato a/).waitFor()
  await attendi(p, 900)
  await foto(p, 'd3-certificato.jpg', { type: 'jpeg', quality: 93 })
  // l'avviso si chiude da solo dopo 7 s: misure e clic in pagina, senza attese dei locator
  META.d3 = await p.evaluate(() => {
    const btn = [...document.querySelectorAll('button')].find((x) => x.innerText.trim() === 'Vedi sulla mappa')
    const card = btn?.closest('[role="status"], .sospeso') ?? btn?.parentElement?.parentElement
    const r = (el) => { const q = el.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height } }
    return { avviso: card && r(card), vedi: btn && r(btn) }
  })
  // D4: "Vedi sulla mappa" vola sul gruppo a zoom 12; mezzi della flotta nascosti (nel trailer partono quelli ricostruiti)
  await p.evaluate(() => [...document.querySelectorAll('button')].find((x) => x.innerText.trim() === 'Vedi sulla mappa')?.click())
  await p.waitForTimeout(600)
  for (const nome of [/Mezzi terrestri/, /Mezzi aerei/]) {
    const riga = p.locator('button.riga').filter({ hasText: nome })
    if ((await riga.getAttribute('aria-pressed')) === 'true') await riga.click()
  }
  await p.locator('[aria-label="Livelli della mappa"] > button').first().click()
  await attendiMappa(p, 3500)
  await foto(p, 'd4-mappa.jpg', { type: 'jpeg', quality: 93 })
  META.d4 = { mappa: await box(p.locator('.maplibregl-canvas')), capo: { lat: capoLat, lon: capoLon }, zoom: 12, padDestra: 412 }
  await ctx.close()
}

await browser.close()
await writeFile(`${OUT}/meta.js`, `// generato da cattura.mjs\nwindow.META = ${JSON.stringify(META, null, 1)}\n`)
console.log('fatto:', OUT)
