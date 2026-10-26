import { test } from 'node:test';
import assert from 'node:assert/strict';

import { DEFAULTS, parseSettings, toQuery } from '../../web/js/settings.js';

test('empty query yields defaults', () => {
  assert.deepEqual(parseSettings(''), { ...DEFAULTS });
});

test('parses all options', () => {
  const s = parseSettings('?theme=black&p=3&scale=0.5&dz=0.1&offset=30&tilt=0&trigger=meter&debug=1');
  assert.deepEqual(s, {
    theme: 'black', player: 3, scale: 0.5, deadzone: 0.1, stickOffset: 30,
    tilt: false, triggerMode: 'meter', debug: true, colors: {},
  });
});

test('parses colors and drops invalid pairs', () => {
  const s = parseSettings('?colors=shell:1E1E1E,accent:%23ff0055,bad:xyz,Upper:ffffff,:123456,sticks');
  assert.deepEqual(s.colors, { shell: '#1e1e1e', accent: '#ff0055' });
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

test('toQuery omits defaults but always keeps theme', () => {
  assert.equal(toQuery({ ...DEFAULTS }), 'theme=white');
});

test('toQuery round-trips through parseSettings', () => {
  const s = {
    theme: 'black', player: 2, scale: 0.5, deadzone: 0.1, stickOffset: 30,
    tilt: false, triggerMode: 'meter', debug: true,
    colors: { shell: '#1e1e1e', highlight: '#ffcc00' },
  };
  assert.deepEqual(parseSettings(toQuery(s)), s);
});

test('toQuery keeps colors readable', () => {
  assert.equal(
    toQuery({ ...DEFAULTS, theme: 'dualsense', colors: { shell: '#1E1E1E', accent: 'ff0055' } }),
    'theme=dualsense&colors=shell:1e1e1e,accent:ff0055',
  );
});
