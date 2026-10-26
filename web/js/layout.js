/* Layout registry and helpers.

Layouts are plain data modules under layouts/. Register new ones here.
*/

import { ds5 } from './layouts/ds5.js';

export const LAYOUTS = Object.freeze({ [ds5.id]: ds5 });
export const DEFAULT_LAYOUT = ds5;

/** Flatten groups into the list of interactive parts. */
export function leafParts(layout) {
  return layout.parts.flatMap((p) => (p.group ? p.children : [p]));
}

/** CSS custom properties pointing each asset variable at the theme's image. */
export function themeVars(layout, themeBaseUrl, ext = 'png') {
  const base = themeBaseUrl.replace(/\/+$/, '');
  return Object.fromEntries(
    Object.entries(layout.assets).map(([name, file]) => [`--${name}`, `url("${base}/${file}.${ext}")`]),
  );
}
