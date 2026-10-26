/* Region recolouring for SVG themes.

A theme's theme.json names regions (shell, accent, ...) and lists, per SVG file,
the exact fill colours each region owns plus an "anchor" (its main colour).
Picking a new colour for a region maps every source colour to a shade of the
target that keeps its relation to the anchor:

  hue        target hue + the source's hue offset from the anchor
  saturation target saturation scaled by source/anchor saturation
  lightness  darker-than-anchor shades scale toward black, lighter ones toward
             white, so shading survives even for very dark or light targets

Regions with "mode": "flat" (e.g. the four PlayStation symbol colours) map
every source colour straight to the target. Pure functions; no DOM.
*/

const HEX = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i;

/** "#AbC" / "aabbcc" -> "#aabbcc", or null when invalid. */
export function normalizeHex(value) {
  const m = HEX.exec(String(value ?? '').trim());
  if (!m) return null;
  const h = m[1].length === 3 ? [...m[1]].map((c) => c + c).join('') : m[1];
  return `#${h.toLowerCase()}`;
}

export function hexToHsl(hex) {
  const n = parseInt(normalizeHex(hex).slice(1), 16);
  const r = ((n >> 16) & 255) / 255;
  const g = ((n >> 8) & 255) / 255;
  const b = (n & 255) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  const d = max - min;
  if (d === 0) return { h: 0, s: 0, l: l * 100 };
  const s = d / (1 - Math.abs(2 * l - 1));
  let h;
  if (max === r) h = ((g - b) / d) % 6;
  else if (max === g) h = (b - r) / d + 2;
  else h = (r - g) / d + 4;
  return { h: (h * 60 + 360) % 360, s: s * 100, l: l * 100 };
}

export function hslToHex({ h, s, l }) {
  const sat = Math.min(100, Math.max(0, s)) / 100;
  const lig = Math.min(100, Math.max(0, l)) / 100;
  const k = (n) => (n + h / 30) % 12;
  const a = sat * Math.min(lig, 1 - lig);
  const f = (n) => lig - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1));
  return `#${[f(0), f(8), f(4)]
    .map((v) => Math.round(v * 255).toString(16).padStart(2, '0')).join('')}`;
}

/** Shade of `target` that stands to `target` as `source` stands to `anchor`. */
export function shade(source, anchor, target) {
  const src = normalizeHex(source);
  const anc = normalizeHex(anchor);
  const tgt = normalizeHex(target);
  if (src === anc) return tgt;

  const s = hexToHsl(src);
  const a = hexToHsl(anc);
  const t = hexToHsl(tgt);

  const hue = a.s > 0 && s.s > 0 ? (t.h + (s.h - a.h) + 360) % 360 : t.h;
  const sat = a.s > 0 ? Math.min(100, t.s * (s.s / a.s)) : t.s;
  let light;
  if (s.l <= a.l) light = a.l > 0 ? t.l * (s.l / a.l) : t.l;
  else light = t.l + (100 - t.l) * ((s.l - a.l) / (100 - a.l));
  return hslToHex({ h: hue, s: sat, l: light });
}

/**
 * Build per-file colour maps from a theme definition and region overrides.
 * Returns { "Base.svg": Map(srcHex -> newHex), ... }; regions without an
 * override (or with an invalid colour) are left untouched.
 */
export function buildReplacements(themeDef, overrides = {}) {
  const out = {};
  for (const [id, region] of Object.entries(themeDef.regions || {})) {
    const target = normalizeHex(overrides[id]);
    if (!target) continue;
    for (const [file, colors] of Object.entries(region.colors)) {
      const map = (out[file] ||= new Map());
      for (const c of colors) {
        const src = normalizeHex(c);
        map.set(src, region.mode === 'flat' ? target : shade(src, region.anchor, target));
      }
    }
  }
  return out;
}

/** Replace #rrggbb colours in one pass (no chained replacements). */
export function recolorSvg(text, replacements) {
  if (!replacements || replacements.size === 0) return text;
  return text.replace(/#[0-9a-f]{6}\b/gi, (hex) => replacements.get(hex.toLowerCase()) ?? hex);
}
