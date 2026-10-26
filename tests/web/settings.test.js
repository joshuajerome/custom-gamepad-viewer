import { test } from 'node:test';
import assert from 'node:assert/strict';

import { DEFAULTS, parseSettings } from '../../web/js/settings.js';

test('empty query yields defaults', () => {
  assert.deepEqual(parseSettings(''), { ...DEFAULTS });
});

test('parses all options', () => {
  const s = parseSettings('?theme=black&p=3&scale=0.5&dz=0.1&offset=30&tilt=0&trigger=meter&debug=1');
  assert.deepEqual(s, {
    theme: 'black', player: 3, scale: 0.5, deadzone: 0.1, stickOffset: 30,
    tilt: false, triggerMode: 'meter', debug: true,
  });
});

test('clamps numeric ranges', () => {
  const s = parseSettings('?p=9&scale=100&dz=-1&offset=999');
  assert.equal(s.player, 4);
  assert.equal(s.scale, 4);
  assert.equal(s.deadzone, 0);
  assert.equal(s.stickOffset, 60);
});

test('invalid values fall back to defaults', () => {
  const s = parseSettings('?p=abc&dz=&trigger=sparkle&scale=fit');
  assert.equal(s.player, 1);
  assert.equal(s.deadzone, DEFAULTS.deadzone);
  assert.equal(s.triggerMode, 'fade');
  assert.equal(s.scale, 'fit');
});

test('rejects theme ids that could escape the themes folder', () => {
  for (const bad of ['../secret', 'a/b', '', '.hidden', 'x'.repeat(65)]) {
    assert.equal(parseSettings(`?theme=${encodeURIComponent(bad)}`).theme, 'white', bad);
  }
});
