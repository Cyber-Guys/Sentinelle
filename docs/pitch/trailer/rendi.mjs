// Rende trailer.html in MP4: compone la colonna sonora nella pagina (OfflineAudioContext) e la salva in colonna.wav,
// poi cattura ogni fotogramma con render(t) e lo passa a ffmpeg su stdin (image2pipe): nessun PNG su disco.
// Uso: node rendi.mjs                          -> sentinelle-trailer.mp4 (30 s, 60 fps)
//      node rendi.mjs --da 10 --a 14 --fps 30  -> anteprima di un tratto (anteprima.mp4)
//      node rendi.mjs --fotogramma 4.2,9.5 --cartella /tmp/x   -> PNG singoli per controllo
import { chromium } from 'playwright'
import { spawn } from 'node:child_process'
import { once } from 'node:events'
import { mkdir, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'

const QUI = new URL('.', import.meta.url).pathname
const arg = (nome, def) => { const i = process.argv.indexOf(`--${nome}`); return i > 0 ? process.argv[i + 1] : def }
const FPS = Number(arg('fps', 60))
const DA = Number(arg('da', 0))
const fotogrammi = arg('fotogramma', null)

const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--hide-scrollbars', '--font-render-hinting=none'] })
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })
page.on('pageerror', (e) => console.log('[errore pagina]', e.message))
page.on('console', (m) => { if (m.type() === 'error') console.log('[console]', m.text()) })
await page.goto(`file://${QUI}trailer.html?render`)
await page.waitForFunction(() => window.pronto === true, null, { timeout: 60000 })
const DURATA = await page.evaluate(() => window.DURATA)
const A = Number(arg('a', DURATA))
const cdp = await page.context().newCDPSession(page)
const cattura = async () => Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64')

if (fotogrammi) {
  const cartella = arg('cartella', `${tmpdir()}/sentinelle-trailer`)
  await mkdir(cartella, { recursive: true })
  for (const t of fotogrammi.split(',').map(Number)) {
    await page.evaluate((t) => window.render(t), t)
    await writeFile(`${cartella}/f-${t.toFixed(2).padStart(5, '0')}.png`, await cattura())
  }
  console.log('fotogrammi in', cartella)
  await browser.close()
  process.exit(0)
}

console.log('colonna sonora...')
const wav = Buffer.from(await page.evaluate(() => window.esportaWav()), 'base64')
await writeFile(`${QUI}colonna.wav`, wav)
console.log('colonna.wav', (wav.length / 1e6).toFixed(1), 'MB')

const parziale = DA > 0 || A < DURATA || FPS !== 60
const uscita = `${QUI}${parziale ? 'anteprima' : 'sentinelle-trailer'}.mp4`
const ff = spawn('ffmpeg', [
  '-y', '-hide_banner', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
  '-ss', String(DA), '-t', String(A - DA), '-i', `${QUI}colonna.wav`,
  '-map', '0:v', '-map', '1:a',
  '-c:v', 'libx264', '-preset', parziale ? 'veryfast' : 'slow', '-crf', parziale ? '20' : '14', '-pix_fmt', 'yuv420p',
  '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
  '-c:a', 'aac', '-b:a', '320k', '-shortest', '-movflags', '+faststart', uscita,
], { stdio: ['pipe', 'inherit', 'inherit'] })
const fine = once(ff, 'close')

const n = Math.round((A - DA) * FPS)
const t0 = Date.now()
for (let i = 0; i < n; i++) {
  await page.evaluate((t) => window.render(t), DA + i / FPS)
  if (!ff.stdin.write(await cattura())) await once(ff.stdin, 'drain')
  if (i % FPS === 0) process.stdout.write(`\r${(DA + i / FPS).toFixed(1)} s  ${(((Date.now() - t0) / 1000) / (i + 1) * 1000).toFixed(0)} ms/fotogramma   `)
}
ff.stdin.end()
const [codice] = await fine
await browser.close()
console.log(`\n${codice === 0 ? 'fatto' : 'ffmpeg ha fallito'}: ${uscita} (${n} fotogrammi in ${((Date.now() - t0) / 1000).toFixed(0)} s)`)
process.exit(codice)
