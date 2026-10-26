import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';

import { buildReplacements, normalizeHex } from '../../web/js/colors.js';
import { DEFAULT_LAYOUT, LAYOUTS } from '../../web/js/layout.js';
import { resolveThemeVars } from '../../web/js/themes.js';

const themesDir = new URL('../../web/themes/', import.meta.url);
const manifest = JSON.parse(readFileSync(new URL('index.json', themesDir), 'utf8'));
const svgThemes = manifest.themes.filter((t) => t.format === 'svg');
const readDef = (id) => JSON.parse(readFileSync(new URL(`${id}/theme.json`, themesDir), 'utf8'));

// fetch() stand-in that serves web/themes/ from disk
async function diskFetch(url) {
  const file = new URL(String(url).replace('https://site.test/themes/', ''), themesDir);
  if (!existsSync(file)) return { ok: false, status: 404 };
  const body = readFileSync(file, 'utf8');
  return { ok: true, status: 200, text: async () => body, json: async () => JSON.parse(body) };
}

test('manifest lists exactly the theme folders', () => {
  const folders = readdirSync(themesDir, { withFileTypes: true })
    .filter((d) => d.isDirectory()).map((d) => d.name).sort();
  assert.deepEqual(manifest.themes.map((t) => t.id).sort(), folders);
});

test('every theme has every asset each layout needs', () => {
  for (const { id, format } of manifest.themes) {
    for (const layout of Object.values(LAYOUTS)) {
      for (const file of Object.values(layout.assets)) {
        const path = `${id}/${file}.${format}`;
        assert.ok(existsSync(new URL(path, themesDir)), `${path} missing`);
      }
    }
  }
});

test('every SVG theme defines regions whose colours exist in the named files', () => {
  assert.ok(svgThemes.length > 0);
  for (const { id } of svgThemes) {
    const def = readDef(id);
    for (const [region, { anchor, colors }] of Object.entries(def.regions)) {
      assert.ok(normalizeHex(anchor), `${id}/${region}: bad anchor`);
      for (const [file, list] of Object.entries(colors)) {
        const svg = readFileSync(new URL(`${id}/${file}`, themesDir), 'utf8').toLowerCase();
        for (const c of list) assert.ok(svg.includes(normalizeHex(c)), `${id}/${file} lacks ${c} (${region})`);
      }
    }
  }
});

test('presets only reference defined regions with valid colours', () => {
  for (const { id } of svgThemes) {
    const def = readDef(id);
    for (const preset of def.presets || []) {
      for (const [region, hex] of Object.entries(preset.colors)) {
        assert.ok(def.regions[region], `${id} preset ${preset.name}: unknown region ${region}`);
        assert.ok(normalizeHex(hex), `${id} preset ${preset.name}: bad colour ${hex}`);
      }
      assert.ok(Object.keys(buildReplacements(def, preset.colors)).length >= 0);
    }
  }
});

test('png themes resolve to absolute image URLs', async () => {
  const vars = await resolveThemeVars(DEFAULT_LAYOUT, 'https://site.test/themes/', 'white', {}, diskFetch);
  assert.equal(vars['--face'], 'url("https://site.test/themes/white/Face.png")');
});

test('svg themes resolve to recoloured data URIs', async () => {
  const vars = await resolveThemeVars(
    DEFAULT_LAYOUT, 'https://site.test/themes/', 'dualsense', { shell: '#123456' }, diskFetch);
  assert.equal(Object.keys(vars).length, Object.keys(DEFAULT_LAYOUT.assets).length);
  const base = decodeURIComponent(vars['--base']);
  assert.ok(base.startsWith('url("data:image/svg+xml;charset=utf-8,<svg'));
  assert.ok(base.includes('#123456'));
  assert.ok(!base.toLowerCase().includes('#ffffff'), 'shell white should be replaced');
});

test('unknown themes fall back to PNG URLs', async () => {
  const vars = await resolveThemeVars(DEFAULT_LAYOUT, 'https://site.test/themes/', 'nope', {}, diskFetch);
  assert.equal(vars['--base'], 'url("https://site.test/themes/nope/Base.png")');
});
