/* Overlay entry point: settings -> layout/theme -> render loop.

Reads the player's gamepad every animation frame via the Gamepad API and
renders it. Browsers only expose a gamepad after its first input, so the
controller shows as disconnected until a button is pressed.

Standalone (offline) builds set window.CGV_STANDALONE = { query, vars } with the
settings and theme baked in, and inline the layout CSS (see standalone.js).
*/

import { DEFAULT_LAYOUT } from './layout.js';
import { parseSettings } from './settings.js';
import { computeFrame, snapshot } from './frame.js';
import { ControllerRenderer } from './renderer.js';
import { resolveThemeVars } from './themes.js';

const standalone = globalThis.CGV_STANDALONE;
const settings = parseSettings(standalone ? standalone.query : location.search);
const layout = DEFAULT_LAYOUT;

if (!standalone) {
  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = layout.cssHref;
  document.head.appendChild(css);
}

const stage = document.getElementById('stage');
stage.style.width = `${layout.width}px`;
stage.style.height = `${layout.height}px`;

const renderer = new ControllerRenderer(layout, stage);
if (standalone) {
  renderer.setVars(standalone.vars);
} else {
  const themesUrl = new URL('themes/', document.baseURI).href;
  resolveThemeVars(layout, themesUrl, settings.theme, settings.colors)
    .then((vars) => renderer.setVars(vars));
}

function applyScale() {
  const s = settings.scale === 'fit'
    ? Math.min(innerWidth / layout.width, innerHeight / layout.height)
    : settings.scale;
  stage.style.transform = `translate(-50%, -50%) scale(${s})`;
}
addEventListener('resize', applyScale);
applyScale();

const debugEl = document.getElementById('debug');
debugEl.hidden = !settings.debug;

function describe(snap) {
  if (!snap) {
    const seen = Array.from(navigator.getGamepads?.() || [])
      .map((g, i) => (g ? `[${i}] ${g.id}` : `[${i}] empty`)).join('\n');
    return `player ${settings.player}: no gamepad (press a button)\n${seen}`;
  }
  const pressed = snap.buttons.map((b, i) => (b.pressed || b.value > 0.05 ? `${i}:${b.value.toFixed(2)}` : null))
    .filter(Boolean).join(' ');
  return [
    `player ${settings.player} -> index ${snap.index}`,
    `id: ${snap.id}`,
    `mapping: ${snap.mapping || '(none - buttons may be misplaced)'}`,
    `buttons: ${pressed || '-'}`,
    `axes: ${snap.axes.map((a) => a.toFixed(2)).join(' ')}`,
  ].join('\n');
}

function tick() {
  const pads = navigator.getGamepads ? navigator.getGamepads() : [];
  const snap = snapshot(pads[settings.player - 1]);
  renderer.render(computeFrame(layout, snap, settings));
  if (settings.debug) debugEl.textContent = describe(snap);
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
