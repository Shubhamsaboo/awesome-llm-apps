// Mermaid flowchart -> looping animated GIF, with no UI and no npm dependencies.
// Opens index.html in headless Chrome (DevTools protocol over Node's built-in WebSocket), draws the text with
// loadTextFlow, renders each frame at an exact time with the app's own export renderer, and joins them with ffmpeg.
//
//   node flow2gif.mjs <in.mmd> <out.gif> [--fps 25] [--period 2] [--scale 1] [--dark] [--mode comets|pulses|neon|dashed] [--page a4|a4-portrait] [--max-per-row N]
//
// --period is one trip of the flow along every arrow, in seconds; the GIF is exactly one period, so it loops seamlessly.
// --page lays the flow out in snaking rows to suit the page shape and pads the image to exactly that shape;
// --max-per-row caps the boxes across a row (down a column for TD).
// Needs Chrome or Chromium (found in the usual places, or set CHROME=<path>) and ffmpeg on PATH.
import { spawn, execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const [input, output, ...rest] = process.argv.slice(2);
if (!input || !output) {
  console.error('usage: node flow2gif.mjs <in.mmd> <out.gif> [--fps 25] [--period 2] [--scale 1] [--dark] [--mode comets|pulses|neon|dashed] [--page a4|a4-portrait] [--max-per-row N]');
  process.exit(2);
}
const opt = (name, def) => {
  const i = rest.indexOf(`--${name}`);
  return i < 0 ? def : Number(rest[i + 1]);
};
const fps = opt('fps', 25);
const period = opt('period', 2);
const scale = opt('scale', 1);
const dark = rest.includes('--dark');
const modeAt = rest.indexOf('--mode');
const mode = modeAt < 0 ? 'comets' : rest[modeAt + 1];  // comets | pulses | neon | dashed
const pageAt = rest.indexOf('--page');
const ASPECTS = { a4: Math.SQRT2, 'a4-portrait': Math.SQRT1_2 };  // A-series pages are 1 : sqrt(2)
const aspect = pageAt < 0 ? 0 : ASPECTS[rest[pageAt + 1]];
if (aspect === undefined) throw new Error(`unknown --page ${rest[pageAt + 1]}: use a4 or a4-portrait`);
const maxPerBand = opt('max-per-row', 0);
const frames = Math.round(fps * period);

const CHROME = process.env.CHROME || [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser'
].find(p => existsSync(p));
if (!CHROME) {
  console.error('Chrome or Chromium not found: set CHROME=<path to the browser executable>');
  process.exit(2);
}
const page = pathToFileURL(join(dirname(fileURLToPath(import.meta.url)), 'index.html')).href;
const work = mkdtempSync(join(tmpdir(), 'excaliflow-'));
const chrome = spawn(CHROME, [
  '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${join(work, 'profile')}`,
  '--no-first-run', '--window-size=1440,900', page
], { stdio: 'ignore' });

try {
  // Chrome writes its debugging port to DevToolsActivePort once it is listening.
  const portFile = join(work, 'profile', 'DevToolsActivePort');
  for (let i = 0; i < 100 && !existsSync(portFile); i++) await new Promise(r => setTimeout(r, 100));
  const port = readFileSync(portFile, 'utf8').split('\n')[0].trim();
  let target;
  for (let i = 0; i < 50 && !target; i++) {
    const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    target = list.find(t => t.type === 'page' && t.url.startsWith('file:'));
    if (!target) await new Promise(r => setTimeout(r, 100));
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = fail; });
  let id = 0;
  const pending = new Map();
  ws.onmessage = m => {
    const msg = JSON.parse(m.data);
    if (pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  };
  const evaluate = async expression => {
    const msg = await new Promise(r => {
      pending.set(++id, r);
      ws.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression, awaitPromise: true, returnByValue: true } }));
    });
    const ex = msg.result?.exceptionDetails;
    if (ex) throw new Error(ex.exception?.description || ex.text);
    return msg.result.result.value;
  };

  for (let i = 0; i < 100 && !(await evaluate(`typeof window.loadTextFlow === 'function' && document.readyState === 'complete'`)); i++) {
    await new Promise(r => setTimeout(r, 100));
  }
  const text = readFileSync(input, 'utf8');
  const warnings = await evaluate(`(async () => {
    setCanvasBackground(${JSON.stringify(dark ? '#000000' : '#ffffff')});
    if (!ALLOWED_FLOW_MODES.has(${JSON.stringify(mode)})) throw new Error('unknown --mode ' + ${JSON.stringify(mode)});
    state.flowMode = ${JSON.stringify(mode)};
    state.flowSpeed = ${1 / (0.55 * period)};  // the renderer moves packets at 0.55 * flowSpeed trips per second
    const warnings = loadTextFlow(${JSON.stringify(text)}, { aspect: ${aspect}, maxPerBand: ${maxPerBand} });
    await Promise.all(['Excalifont', 'Virgil', 'Cascadia'].map(f => document.fonts.load('20px ' + f)));
    await document.fonts.ready;
    ShapeCache.clear();
    const bounds = getDiagramExportBounds(48);
    if (${aspect} > 0) {  // pad the short side, centred, so the image is exactly the page shape
      const grow = Math.max(bounds.width, bounds.height * ${aspect}) / bounds.width;
      const w = bounds.width * grow, h = w / ${aspect};
      Object.assign(bounds, { x: bounds.x - (w - bounds.width) / 2, y: bounds.y - (h - bounds.height) / 2, width: w, height: h });
    }
    const c = document.createElement('canvas');
    c.width = Math.round(bounds.width * ${scale});
    c.height = Math.round(bounds.height * ${scale});
    window.__gif = { c, ctx: c.getContext('2d'), bounds };
    return warnings;
  })()`);
  warnings.forEach(w => console.warn(`warning: ${w}`));

  // One warm-up period so the arrival glows are already in their steady state on frame 0.
  for (let f = 0; f < frames; f++) {
    await evaluate(`renderSceneToExportCtx(__gif.ctx, __gif.c, __gif.bounds, ${scale}, ${f / fps})`);
  }
  for (let f = 0; f < frames; f++) {
    const png = await evaluate(`renderSceneToExportCtx(__gif.ctx, __gif.c, __gif.bounds, ${scale}, ${period + f / fps}), __gif.c.toDataURL('image/png')`);
    writeFileSync(join(work, `f${String(f).padStart(4, '0')}.png`), Buffer.from(png.split(',')[1], 'base64'));
  }
  ws.close();

  execFileSync('ffmpeg', [
    '-y', '-loglevel', 'error', '-framerate', String(fps), '-i', join(work, 'f%04d.png'),
    '-vf', 'split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a',
    '-loop', '0', resolve(output)
  ]);
  console.log(`wrote ${output}: ${frames} frames at ${fps} fps, ${period} s loop`);
} finally {
  chrome.kill();
  await new Promise(r => setTimeout(r, 300));
  rmSync(work, { recursive: true, force: true });
}
