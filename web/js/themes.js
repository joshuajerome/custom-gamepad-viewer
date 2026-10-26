/* Theme loading: manifest -> CSS custom properties for a layout.

PNG themes point the layout's variables at image URLs. SVG themes (with a
theme.json defining colour regions) are fetched, recoloured with the requested
region overrides, and inlined as data: URIs. Any fetch failure falls back to
treating the theme as plain PNGs, so the overlay always renders something.
*/

import { buildReplacements, recolorSvg } from './colors.js';
import { themeVars } from './layout.js';

const FORMATS = { png: 'png', svg: 'svg' };

async function getJson(fetchFn, url) {
  const res = await fetchFn(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.json();
}

/** themes/index.json -> [{ id, name, format }] ([] when unavailable). */
export async function loadThemeIndex(themesUrl, fetchFn = fetch) {
  try {
    const { themes } = await getJson(fetchFn, new URL('index.json', themesUrl));
    return themes.map((t) => ({ ...t, format: FORMATS[t.format] || 'png' }));
  } catch {
    return [];
  }
}

/** themes/<id>/theme.json (regions, presets) or null for themes without one. */
export async function loadThemeDef(themesUrl, id, fetchFn = fetch) {
  try {
    return await getJson(fetchFn, new URL(`${id}/theme.json`, themesUrl));
  } catch {
    return null;
  }
}

function svgDataUri(text) {
  return `url("data:image/svg+xml;charset=utf-8,${encodeURIComponent(text)}")`;
}

/**
 * Resolve the CSS variables for `layout` using theme `id`.
 * `themesUrl` must be an absolute URL ending in "/" (e.g. .../themes/).
 */
export async function resolveThemeVars(layout, themesUrl, id, colors = {}, fetchFn = fetch) {
  const index = await loadThemeIndex(themesUrl, fetchFn);
  const entry = index.find((t) => t.id === id) || { id, format: 'png' };
  const base = new URL(`${id}/`, themesUrl).href;
  if (entry.format !== 'svg') return themeVars(layout, base, 'png');

  try {
    const def = (await loadThemeDef(themesUrl, id, fetchFn)) || { regions: {} };
    const replacements = buildReplacements(def, colors);
    const entries = await Promise.all(Object.entries(layout.assets).map(async ([name, file]) => {
      const res = await fetchFn(new URL(`${file}.svg`, base), { cache: 'no-cache' });
      if (!res.ok) throw new Error(`${file}.svg: HTTP ${res.status}`);
      const svg = recolorSvg(await res.text(), replacements[`${file}.svg`]);
      return [`--${name}`, svgDataUri(svg)];
    }));
    return Object.fromEntries(entries);
  } catch {
    return themeVars(layout, base, 'svg');
  }
}
