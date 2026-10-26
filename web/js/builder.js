/* URL builder page.

Form state <-> settings object <-> overlay URL. The preview iframe loads the
real overlay.html with the same query, so it matches the browser source exactly.
State is remembered per browser (localStorage) and can be seeded from this
page's own query string, e.g. index.html?theme=black&p=2.

Colour overrides live outside the <form> (in `colors`) because the available
regions depend on the selected theme's theme.json.
*/

import { normalizeHex } from './colors.js';
import { DEFAULT_LAYOUT } from './layout.js';
import { DEFAULTS, parseSettings, toQuery } from './settings.js';
import { buildStandalone } from './standalone.js';
import { loadThemeDef, loadThemeIndex } from './themes.js';

const STORAGE_KEY = 'cgv.builder';
const layout = DEFAULT_LAYOUT;
const themesUrl = new URL('themes/', document.baseURI).href;

let themes = [];
let themeDef = null; // theme.json of the selected theme, when it has colour regions
let colors = {}; // region id -> "#rrggbb" overrides

const form = document.getElementById('form');
const els = {
  theme: document.getElementById('theme'),
  scale: document.getElementById('scale'),
  deadzone: document.getElementById('deadzone'),
  stickOffset: document.getElementById('stickOffset'),
  tilt: document.getElementById('tilt'),
  url: document.getElementById('url'),
  copy: document.getElementById('copy'),
  size: document.getElementById('size'),
  open: document.getElementById('open'),
  openDebug: document.getElementById('open-debug'),
  preview: document.getElementById('preview'),
  detect: document.getElementById('detect'),
  reset: document.getElementById('reset'),
  download: document.getElementById('download'),
  downloadStatus: document.getElementById('download-status'),
  colors: document.getElementById('colors'),
  presets: document.getElementById('presets'),
  regions: document.getElementById('regions'),
};

function loadStored() {
  try {
    return localStorage.getItem(STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

function store(query) {
  try {
    localStorage.setItem(STORAGE_KEY, query);
  } catch {
    // storage blocked (private mode, OBS dock); builder still works
  }
}

function radio(name, value) {
  const input = form.querySelector(`input[name="${name}"][value="${value}"]`);
  if (input) input.checked = true;
}

function writeForm(s) {
  els.theme.value = s.theme;
  radio('player', s.player);
  radio('triggerMode', s.triggerMode);
  els.scale.value = String(s.scale);
  if (els.scale.value !== String(s.scale)) {
    // custom numeric scale from a pasted URL: keep it selectable
    els.scale.add(new Option(`${Math.round(s.scale * 100)}%`, String(s.scale)));
    els.scale.value = String(s.scale);
  }
  els.deadzone.value = s.deadzone;
  els.stickOffset.value = s.stickOffset;
  els.tilt.checked = s.tilt;
  colors = { ...s.colors };
}

/** Overrides that apply to the selected theme (drops regions it doesn't have). */
function activeColors() {
  if (!themeDef) return {};
  return Object.fromEntries(Object.entries(colors).filter(([id]) => themeDef.regions[id]));
}

function sameColors(a, b) {
  const ka = Object.keys(a);
  return ka.length === Object.keys(b).length && ka.every((k) => normalizeHex(a[k]) === normalizeHex(b[k]));
}

function renderColors() {
  els.colors.hidden = !themeDef;
  els.presets.replaceChildren();
  els.regions.replaceChildren();
  if (!themeDef) return;

  const current = activeColors();
  for (const preset of themeDef.presets || []) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'preset';
    btn.setAttribute('aria-pressed', String(sameColors(current, preset.colors)));
    const swatch = document.createElement('span');
    swatch.className = 'swatch';
    const pick = (id) => preset.colors[id] || themeDef.regions[id]?.anchor || '#000000';
    swatch.style.background =
      `linear-gradient(135deg, ${pick('shell')} 0 50%, ${pick('accent')} 50% 75%, ${pick('highlight')} 75%)`;
    btn.append(swatch, preset.name);
    btn.addEventListener('click', () => {
      colors = { ...preset.colors };
      renderColors();
      update();
    });
    els.presets.append(btn);
  }

  for (const [id, region] of Object.entries(themeDef.regions)) {
    const row = document.createElement('div');
    row.className = 'region';
    row.classList.toggle('custom', Boolean(current[id]));

    const input = document.createElement('input');
    input.type = 'color';
    input.id = `color-${id}`;
    input.value = current[id] || normalizeHex(region.anchor);

    const label = document.createElement('label');
    label.htmlFor = input.id;
    label.textContent = region.label || id;
    if (region.hint) label.title = region.hint;

    const reset = document.createElement('button');
    reset.type = 'button';
    reset.className = 'region-reset';
    reset.textContent = 'Reset';
    reset.setAttribute('aria-label', `Reset ${region.label || id} to the original colour`);
    reset.addEventListener('click', () => {
      delete colors[id];
      renderColors();
      update();
    });

    input.addEventListener('input', (e) => {
      e.stopPropagation(); // handled here, not by the form listener
      colors[id] = input.value;
      row.classList.add('custom');
      for (const b of els.presets.children) b.setAttribute('aria-pressed', 'false');
      update();
    });

    row.append(input, label, reset);
    els.regions.append(row);
  }
}

async function selectTheme(id) {
  const entry = themes.find((t) => t.id === id);
  themeDef = entry?.format === 'svg' ? await loadThemeDef(themesUrl, id) : null;
  if (themeDef && !themeDef.regions) themeDef = null;
  renderColors();
}

function readForm() {
  const data = new FormData(form);
  return {
    theme: data.get('theme'),
    player: Number(data.get('player')),
    scale: data.get('scale') === 'fit' ? 'fit' : Number(data.get('scale')),
    deadzone: Number(data.get('deadzone')),
    stickOffset: Number(data.get('stickOffset')),
    tilt: els.tilt.checked,
    triggerMode: data.get('triggerMode'),
    debug: false,
    colors: activeColors(),
  };
}

function overlayUrl(query) {
  return new URL(`overlay.html${query ? `?${query}` : ''}`, location.href).href;
}

function sourceSize(scale) {
  if (scale === 'fit') return [layout.width, layout.height];
  return [Math.round(layout.width * scale), Math.round(layout.height * scale)];
}

let previewTimer = 0;

function update({ immediatePreview = false } = {}) {
  const s = readForm();
  const query = toQuery(s);
  const url = overlayUrl(query);

  els.url.value = url;
  els.open.href = url;
  els.openDebug.href = overlayUrl(toQuery({ ...s, debug: true }));
  document.getElementById('deadzone-out').textContent = s.deadzone.toFixed(2);
  document.getElementById('stickOffset-out').textContent = `${s.stickOffset}px`;

  const [w, h] = sourceSize(s.scale);
  els.size.innerHTML = s.scale === 'fit'
    ? `Browser source size: <b>${w} × ${h}</b> (any size works; the controller scales to fit)`
    : `Browser source size: <b>${w} × ${h}</b>`;

  store(query);

  // The preview box stands in for a correctly sized browser source, which looks
  // identical to "fit" at any scale. Debounce reloads while dragging sliders.
  const previewUrl = overlayUrl(toQuery({ ...s, scale: 'fit' }));
  clearTimeout(previewTimer);
  const reload = () => {
    if (els.preview.src !== previewUrl) els.preview.src = previewUrl;
  };
  if (immediatePreview) reload();
  else previewTimer = setTimeout(reload, 250);
}

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(els.url.value);
  } catch {
    els.url.select();
    document.execCommand('copy');
  }
  els.copy.textContent = 'Copied';
  setTimeout(() => { els.copy.textContent = 'Copy'; }, 1500);
}

async function downloadStandalone() {
  const settings = readForm();
  els.download.disabled = true;
  els.downloadStatus.textContent = 'Building…';
  try {
    const html = await buildStandalone({
      layout, settings, query: toQuery(settings), siteUrl: new URL('./', location.href).href,
    });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([html], { type: 'text/html' }));
    link.download = `gamepad-overlay-${settings.theme}-p${settings.player}.html`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 10000);
    els.downloadStatus.textContent = `Saved ${link.download} (${Math.round(html.length / 1024)} KB).`;
  } catch (err) {
    els.downloadStatus.textContent = `Couldn't build the file: ${err.message}`;
  } finally {
    els.download.disabled = false;
  }
}

// Slot detection: the first gamepad with input wins.
function watchForInput() {
  let lastIndex = -1;
  const poll = () => {
    const pads = navigator.getGamepads ? Array.from(navigator.getGamepads()) : [];
    const active = pads.find((g) => g && (
      g.buttons.some((b) => b.pressed) || g.axes.some((a) => Math.abs(a) > 0.5)));
    if (active && active.index !== lastIndex) {
      lastIndex = active.index;
      const player = active.index + 1;
      if (player <= 4) {
        radio('player', player);
        update();
        els.detect.textContent = `Detected "${active.id}" in slot P${player}.`;
      } else {
        els.detect.textContent = `Controller is in slot ${player}; only P1 to P4 are supported.`;
      }
    }
    requestAnimationFrame(poll);
  };
  requestAnimationFrame(poll);
}

async function init() {
  themes = await loadThemeIndex(themesUrl);
  if (themes.length === 0) themes = [{ id: DEFAULTS.theme, name: DEFAULTS.theme, format: 'png' }];
  for (const t of themes) els.theme.add(new Option(t.name, t.id));

  const seed = location.search || loadStored();
  const initial = parseSettings(seed);
  // Without an explicit theme, start on the featured (first) theme; overlay URLs
  // keep their own default.
  const named = new URLSearchParams(seed).has('theme');
  if (!named || !themes.some((t) => t.id === initial.theme)) initial.theme = themes[0].id;
  writeForm(initial);
  await selectTheme(initial.theme);
  update({ immediatePreview: true });

  form.addEventListener('input', () => update());
  form.addEventListener('change', () => update());
  els.theme.addEventListener('change', async () => {
    await selectTheme(els.theme.value);
    update({ immediatePreview: true });
  });
  els.copy.addEventListener('click', copyUrl);
  els.download.addEventListener('click', downloadStandalone);
  els.url.addEventListener('focus', () => els.url.select());
  els.reset.addEventListener('click', async () => {
    writeForm({ ...DEFAULTS, theme: themes[0].id });
    await selectTheme(themes[0].id);
    update({ immediatePreview: true });
  });
  watchForInput();
}

init();
