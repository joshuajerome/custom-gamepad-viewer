/* Overlay settings parsed from the URL query string.

All configuration lives in the URL so a Streamlabs/OBS browser source is fully
described by the address pasted into it (no server, no storage).

  theme    skin folder under themes/            (default "white")
  p        player slot 1-4                      (default 1)
  scale    "fit" or a number, e.g. 0.5          (default "fit")
  dz       stick deadzone 0-0.9                 (default 0.25)
  offset   max stick travel in px 0-60          (default 22)
  tilt     0 disables the stick tilt effect     (default 1)
  trigger  "fade" (opacity) or "meter" (fill)   (default "fade")
  debug    1 shows raw gamepad input            (default 0)
*/

export const DEFAULTS = Object.freeze({
  theme: 'white',
  player: 1,
  scale: 'fit',
  deadzone: 0.25,
  stickOffset: 22,
  tilt: true,
  triggerMode: 'fade',
  debug: false,
});

const THEME_ID = /^[a-z0-9][a-z0-9_-]{0,63}$/i;

function num(raw, fallback, min, max) {
  if (raw === null || raw.trim() === '') return fallback;
  const v = Number(raw);
  if (!Number.isFinite(v)) return fallback;
  return Math.min(max, Math.max(min, v));
}

function flag(raw, fallback) {
  if (raw === null) return fallback;
  return !['0', 'false', 'no', 'off'].includes(raw.toLowerCase());
}

/** Parse a query string (or URLSearchParams) into a complete settings object. */
export function parseSettings(search) {
  const q = search instanceof URLSearchParams ? search : new URLSearchParams(search);

  const theme = q.get('theme');
  const scaleRaw = q.get('scale');

  return {
    theme: theme && THEME_ID.test(theme) ? theme : DEFAULTS.theme,
    player: Math.round(num(q.get('p'), DEFAULTS.player, 1, 4)),
    scale: !scaleRaw || scaleRaw === 'fit' ? 'fit' : num(scaleRaw, 1, 0.1, 4),
    deadzone: num(q.get('dz'), DEFAULTS.deadzone, 0, 0.9),
    stickOffset: num(q.get('offset'), DEFAULTS.stickOffset, 0, 60),
    tilt: flag(q.get('tilt'), DEFAULTS.tilt),
    triggerMode: q.get('trigger') === 'meter' ? 'meter' : 'fade',
    debug: flag(q.get('debug'), DEFAULTS.debug),
  };
}

// settings key -> [query param, serializer]; inverse of parseSettings
const PARAMS = {
  theme: ['theme', String],
  player: ['p', String],
  scale: ['scale', String],
  deadzone: ['dz', String],
  stickOffset: ['offset', String],
  tilt: ['tilt', (v) => (v ? '1' : '0')],
  triggerMode: ['trigger', String],
  debug: ['debug', (v) => (v ? '1' : '0')],
};

/** Serialize settings to a query string, omitting defaults (theme is always kept). */
export function toQuery(settings) {
  const q = new URLSearchParams();
  for (const [key, [param, serialize]] of Object.entries(PARAMS)) {
    const value = settings[key];
    if (value === undefined || (value === DEFAULTS[key] && key !== 'theme')) continue;
    q.set(param, serialize(value));
  }
  return q.toString();
}
