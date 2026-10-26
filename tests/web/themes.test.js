import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';

import { LAYOUTS } from '../../web/js/layout.js';

const themesDir = new URL('../../web/themes/', import.meta.url);
const manifest = JSON.parse(readFileSync(new URL('index.json', themesDir), 'utf8'));

test('manifest lists exactly the theme folders', () => {
  const folders = readdirSync(themesDir, { withFileTypes: true })
    .filter((d) => d.isDirectory()).map((d) => d.name).sort();
  assert.deepEqual(manifest.themes.map((t) => t.id).sort(), folders);
});

test('every theme has every asset each layout needs', () => {
  for (const { id } of manifest.themes) {
    for (const layout of Object.values(LAYOUTS)) {
      for (const file of Object.values(layout.assets)) {
        assert.ok(existsSync(new URL(`${id}/${file}`, themesDir)), `${id}/${file} missing`);
      }
    }
  }
});
