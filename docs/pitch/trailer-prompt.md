<inputs>
Project: "Sentinelle" (working name; if the repo shows a final name, use it). It is a real, running product:
citizen web app (phone UI, Italian) at http://localhost:3000 and operators dashboard at http://localhost:3001/cruscotto.
Sources of truth, in order: AGENTS.md, docs/specifiche/2026-10-16-webapp-cittadino.md, docs/specifiche/2026-10-09-sentinelle-incendi.md,
docs/interfaccia/linguaggio-visivo-webapp.md, webapp/app (pages, utils/tipi.ts, assets/css/tema.css), docs/materiali/README.md.
Audience: hackathon jury, film projected in a room. They score 1-5 on idea, prototype, novelty, social impact, team, presentation.
In 30 seconds the film must make idea, novelty and impact obvious and prove the prototype is real.
Canvas: 1920x1080, 60 fps, 30 s at 120 BPM (15 bars). A 1080x1920 cut only after I approve the first.
All on-screen copy in Italian, short, no jargon.
Ask me ONCE, in a single message before the storyboard, for what is missing: team name and member names, hackathon name,
call to action. If I skip: no team card, CTA = project name + one line.
Assets (default: capture them yourself): 3-6 real screenshots from the running apps (use ?pos=39.4216,8.9223&dir=45; seed only users
named "(demo)" and delete them afterwards; never touch other rows; never modify product code), logo = webapp/public/icona.svg
(red rounded square, white flame outline), colors and font from tema.css (Atkinson Hyperiles locally),
and a track with a clear beat composed in code.
</inputs>

<facts>
Only these may appear on screen; each is already in the repo or visible in the running app. Anything else is invented: do not.
- A citizen opens the app, taps SEGNALA, takes a photo, picks Incendio / Fumo / Terreno a rischio, adds an optional note (voice dictation), sends.
  Position and the direction the phone faces travel with the report.
- The map: my position with a look-direction cone, satellite or standard view, risk zones by level, circles around active reports,
  pins that merge into one when zoomed out, a danger banner ("Incendio a 1,0 km: da Casa, verso nord-est").
- Saved places (Casa, Terreno, Vigna) with alerts ranked Urgente / Importante / Informazione. Other citizens confirm "Lo vedo anch'io" / "Non c'è più".
- Operators receive the report already cross-checked against satellite hotspots (NASA FIRMS), weather, vegetation (Corine) and the CFVA
  fire history, ordered by priority. Their confirmation ("Mezzi sul posto") reaches the citizen's phone live.
- It runs in a phone browser, no install; the base map also works offline.
- Demo dataset: 377 comuni, 27.544 historical fires (verify in the repo or DB before using).
- NOT in the app today, never show: missions, gamification, points, leaderboards, push nsponse times, any statistic.
</facts>

<direction>
A 30-second launch film that persuades the jury this is an innovative, working idea. Research the repo and both running apps first: what it
does, who it is for, its real screens and brand. Show me what you found. Never invent screens, features or numbers.
Pick one through-line object from the product itself and make every scene a transformation of it: it starts in the UI, changes shape or role
in each scene, and becomes the logo on the end card. Name it before you storyboard. Strong candidate: the red report pin (flame on a
brace-red #c4360f disk with its pulse ring), which turns from circle into the logo's squircle. Alternative: the look-direction cone.
Rebuild the real UI as vector layers (HTML/SVG from the real tokens and strings) so its parts move on their own; never slide a flat
screenshot in. Satellite imagery is the only raster: capture it once at 2x as stills and never hit the network while rendering.
A cursor drives every interaction with real clicks and drags; the camera zooms screen-studio style so each moment fills the frame.
In landscape, use the side space for the film's own kinetic type and keep the phone UI l
Brand: tema.css colors and Atkinson Hyperlegible Next for the film's own type. One accent color (#c4360f), used only on the through-line
object and the key word; lots of empty space. Replicas keep the real UI's own typefaces; if the dashboard uses another font, it stays inside its replica.
Motion rules: springs with at most a small overshoot; nothing appears from nothing (it gby a mask); the camera
never sits still (push 1.0 to 1.04 across a scene, each scene starts at the zoom the last one ended on); something changes on every beat.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, chromatic aberration, iridescent or generic gradients, crossfades,
bouncy easing, holds longer than half a second, anything that looks like a template. The pulse ring is a hard-edged ring, not a glow.
</direction>

<liquid-glass>
The film's own layers (hook plate, source chips, callouts, the CTA capsule, the phone bezel's reflections) use an Apple-style Liquid Glass
material. The product UI itself stays exactly as shipped: never restyle real screens.
Read first: ~/.claude/skills/taste/SKILL.md, Appendix C ("honest web approximation"), an
~/.claude/skills/ui-ux-pro-max/data/styles.csv. Where the latter asks for chromatic aberration or iridescent gradients, ignore it: banned here.
Material: neutral translucent fill (white 10-18%), backdrop-filter blur(24px) saturate(180%), a 1px inner rim highlight brighter at the
light-facing corner (a rim, not a glow), a soft contact shadow, capsules and concentric radii. It lenses what is behind it: scale the
backdrop 3-6% inside the glass and shift it against the pan so it reads as refraction (through
backdrop-filter in Chromium; if it does not render, fall back to blur + scaled backdrop).
Glass shapes merge and split like liquid: animate border-radius, width and height, plus a blur+contrast "gooey" merge, all computed from
time. Glass only over busy backgrounds (satellite, photo); on flat backgrounds use solid ink. Text on glass keeps 7:1 contrast.
Comment in code that this is a web approximation of Liquid Glass, not Apple's material.
</liquid-glass>

<structure>
120 BPM (1 bar = 2 s). Write a timed storyboard first, as a table: bar.beat, seconds, camera, what changes, Italian on-screen copy, sound.
Then build exactly that.
Hook (bars 1-2): the problem in three to five words, in big type that the through-line object interrupts. Example: "Chi lo vede per primo?"
Middle (bars 3-12): four moments, each begins with the object turning into the next UI element and lands one readable idea:
 A. Three taps: SEGNALA, photo, type, send. The pin is born from the shutter. (the idea)
 B. Verified before it alerts: the report crosses FIRMS, weather, Corine, CFVA as glass chips and gets a priority. (novelty)
 C. Two apps, one truth: the dashboard queue reorders by priority; the operator confirms; "Mezzi sul posto" lights up on the citizen's phone. (prototype)
 D. Around you: the map pulls back, circles, merging pins, danger banner, Casa and Terreno alerts. (social impact)
Payoff (bars 13-15): the strongest moment on the biggest beat (suggested: C, phone and dashboard changing on the same beat), then the object
becomes the logo and the end card: name, a one-line call to action, team line if given, and a tiny credit line
"Mappa © OpenStreetMap contributors, Protomaps. Immagini satellitari Esri, Maxar, Earthstar Geographics." (team).
</structure>

<build>
1. One HTML file at 1920x1080 in docs/pitch/trailer/. Every style is computed from time  animations, no timers,
   no state carried between frames. Bundle every script, font and image locally; no CDN.
2. Spring and exponential easing as functions of time. Blur follows speed and direction on fast moves.
3. Soundtrack in code with the Web Audio API (OfflineAudioContext): a kick on every beat and a hit on each scene change. Render to WAV.
4. Render with Playwright at 60 fps, 3 subframes per frame blended with ffmpeg tmix for io into an MP4.
5. Before the full render, render one frame per beat and look at them as a contact sheet. Fix anything cluttered, off the beat, overlapping,
   hard to read or low contrast on glass. Then render.
6. Do not commit, do not touch STATO.md, leave the Docker stack running. Save the storyboard table as docs/pitch/trailer/storyboard.md.
</build>

<gotchas>
Measure element positions at runtime for match cuts instead of hard-coding them. When a shape fills the frame, scale it past all four
corners. Give outgoing and incoming text separate timing so letters never overlap. Never put will-change on anything the camera scales, or
text renders blurry. Apply the camera scale on a wrapper and keep the glass blur radius constant in screen space.
</gotchas>

<start>
Show me what you found, the through-line object and the beat-by-beat storyboard, then build it without asking me anything else.
Give me the final MP4 and the contact sheet.
</start>
