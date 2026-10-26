import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  buildReplacements, hexToHsl, hslToHex, normalizeHex, recolorSvg, shade,
} from '../../web/js/colors.js';

test('normalizeHex accepts 3/6 digit forms with or without #', () => {
  assert.equal(normalizeHex('#ABC'), '#aabbcc');
  assert.equal(normalizeHex('1e1e1e'), '#1e1e1e');
  for (const bad of ['', 'red', '#12345', '#ggg', null, undefined]) assert.equal(normalizeHex(bad), null);
});

test('hsl round-trips', () => {
  for (const hex of ['#000000', '#ffffff', '#c1272d', '#3ed8d2', '#7a55c8', '#101010']) {
    assert.equal(hslToHex(hexToHsl(hex)), hex);
  }
});

test('the anchor maps exactly to the target', () => {
  assert.equal(shade('#c1272d', '#c1272d', '#00ff88'), '#00ff88');
});

test('darker and lighter shades stay darker and lighter than the target', () => {
  const target = '#3366cc';
  const t = hexToHsl(target).l;
  assert.ok(hexToHsl(shade('#9e1f20', '#c1272d', target)).l < t); // shadow
  assert.ok(hexToHsl(shade('#c6383d', '#c1272d', target)).l > t); // highlight
});

test('shading survives very light and very dark targets', () => {
  // lighter-than-anchor shades of a white target stay white rather than overflowing
  assert.equal(shade('#2b2b2b', '#101010', '#ffffff'), '#ffffff');
  // darker shade of a black anchor region cannot exist; lighter one lifts off black
  assert.notEqual(shade('#181818', '#101010', '#000000'), '#000000');
});

test('buildReplacements honours flat mode and ignores bad overrides', () => {
  const def = {
    regions: {
      accent: { anchor: '#c1272d', colors: { 'A.svg': ['#c1272d', '#9e1f20'] } },
      symbols: { mode: 'flat', anchor: '#f16667', colors: { 'B.svg': ['#66c194', '#f16667'] } },
      untouched: { anchor: '#ffffff', colors: { 'A.svg': ['#ffffff'] } },
    },
  };
  const r = buildReplacements(def, { accent: '#0000ff', symbols: '#ffffff', untouched: 'nope' });
  assert.equal(r['A.svg'].get('#c1272d'), '#0000ff');
  assert.notEqual(r['A.svg'].get('#9e1f20'), '#0000ff');
  assert.equal(r['A.svg'].has('#ffffff'), false);
  assert.deepEqual([...r['B.svg'].values()], ['#ffffff', '#ffffff']);
});

test('recolorSvg replaces in one pass without chaining', () => {
  const map = new Map([['#aaaaaa', '#bbbbbb'], ['#bbbbbb', '#cccccc']]);
  assert.equal(
    recolorSvg('.a{fill:#AAAAAA}.b{fill:#bbbbbb}<stop stop-color="#aaaaaa"/>', map),
    '.a{fill:#bbbbbb}.b{fill:#cccccc}<stop stop-color="#bbbbbb"/>',
  );
  assert.equal(recolorSvg('#aaaaaa', new Map()), '#aaaaaa');
});
