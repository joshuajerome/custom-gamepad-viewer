/* URL builder page.

Form state <-> settings object <-> overlay URL. The preview iframe loads the
real overlay.html with the same query, so it matches the browser source exactly.
State is remembered per browser (localStorage) and can be seeded from this
page's own query string, e.g. index.html?theme=black&p=2.
*/

import { DEFAULT_LAYOUT } from './layout.js';
import { DEFAULTS, parseSettings, toQuery } from './settings.js';

const STORAGE_KEY = 'cgv.builder';
const layout = DEFAULT_LAYOUT;

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

async function loadThemes() {
  try {
    const res = await fetch('themes/index.json', { cache: 'no-store' });
    if (res.ok) return (await res.json()).themes;
  } catch {
    // fall through to the built-in default
  }
  return [{ id: DEFAULTS.theme, name: DEFAULTS.theme }];
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
  const themes = await loadThemes();
  for (const t of themes) els.theme.add(new Option(t.name, t.id));

  const initial = parseSettings(location.search || loadStored());
  if (!themes.some((t) => t.id === initial.theme)) initial.theme = themes[0].id;
  writeForm(initial);
  update({ immediatePreview: true });

  form.addEventListener('input', () => update());
  form.addEventListener('change', () => update());
  els.copy.addEventListener('click', copyUrl);
  els.url.addEventListener('focus', () => els.url.select());
  els.reset.addEventListener('click', () => {
    writeForm({ ...DEFAULTS, theme: themes[0].id });
    update({ immediatePreview: true });
  });
  watchForInput();
}

init();
