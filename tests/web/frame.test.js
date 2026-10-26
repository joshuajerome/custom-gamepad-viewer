import { test } from 'node:test';
import assert from 'node:assert/strict';

import { computeFrame, snapshot } from '../../web/js/frame.js';
import { DEFAULT_LAYOUT, leafParts, themeVars } from '../../web/js/layout.js';
import { DEFAULTS } from '../../web/js/settings.js';

function pad({ buttons = {}, axes = [0, 0, 0, 0] } = {}) {
  const list = Array.from({ length: 18 }, (_, i) => {
    const v = buttons[i] ?? 0;
    return { pressed: v >= 0.5, value: v };
  });
  return { id: 'test pad', index: 0, mapping: 'standard', connected: true, buttons: list, axes };
}

const frameFor = (p, overrides = {}) =>
  computeFrame(DEFAULT_LAYOUT, snapshot(p), { ...DEFAULTS, ...overrides });

test('no gamepad renders disconnected', () => {
  assert.deepEqual(computeFrame(DEFAULT_LAYOUT, snapshot(null), DEFAULTS), { connected: false, parts: {} });
  assert.equal(snapshot({ connected: false }), null);
});

test('every layout part gets state', () => {
  const f = frameFor(pad());
  assert.deepEqual(Object.keys(f.parts).sort(), leafParts(DEFAULT_LAYOUT).map((p) => p.key).sort());
});

test('standard mapping drives face buttons and dpad', () => {
  const f = frameFor(pad({ buttons: { 0: 1, 3: 1, 12: 1, 16: 1 } }));
  assert.equal(f.parts.cross.pressed, true);
  assert.equal(f.parts.triangle.pressed, true);
  assert.equal(f.parts.up.pressed, true);
  assert.equal(f.parts.ps.pressed, true);
  assert.equal(f.parts.circle.pressed, false);
  assert.equal(f.parts.down.pressed, false);
});

test('sticks slide by axis * offset and tilt', () => {
  const f = frameFor(pad({ axes: [1, -0.5, 0, 0] }));
  assert.equal(f.parts.ls.marginLeft, '22px');
  assert.equal(f.parts.ls.marginTop, '-11px');
  assert.equal(f.parts.ls.transform, 'rotateX(11deg) rotateY(22deg)');
  assert.equal(f.parts.rs.marginLeft, '0px');
});

test('sticks inside the deadzone stay centred', () => {
  const f = frameFor(pad({ axes: [0.15, 0.15, 0, 0] }));
  assert.equal(f.parts.ls.marginLeft, '0px');
  assert.equal(f.parts.ls.marginTop, '0px');
});

test('tilt can be disabled and offset changed', () => {
  const f = frameFor(pad({ axes: [0, 0, -1, 0] }), { tilt: false, stickOffset: 10 });
  assert.equal(f.parts.rs.marginLeft, '-10px');
  assert.equal(f.parts.rs.transform, '');
});

test('stick click marks the stick pressed', () => {
  assert.equal(frameFor(pad({ buttons: { 10: 1 } })).parts.ls.pressed, true);
});

test('triggers fade with analog value by default', () => {
  const f = frameFor(pad({ buttons: { 6: 0.4, 7: 1 } }));
  assert.deepEqual(f.parts.l2, { opacity: '0.4', clipPath: '' });
  assert.deepEqual(f.parts.r2, { opacity: '1', clipPath: '' });
});

test('meter mode fills triggers from the bottom', () => {
  const f = frameFor(pad({ buttons: { 6: 0.25 } }), { triggerMode: 'meter' });
  assert.deepEqual(f.parts.l2, { opacity: '1', clipPath: 'inset(75% 0 0 0)' });
});

test('theme vars point at the theme folder', () => {
  const vars = themeVars(DEFAULT_LAYOUT, 'themes/white/');
  assert.equal(vars['--face'], 'url("themes/white/Face.png")');
  assert.equal(Object.keys(vars).length, 10);
});
