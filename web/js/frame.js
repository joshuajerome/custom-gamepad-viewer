/* Pure input -> visual state mapping.

Turns a gamepad snapshot into per-part visual properties. No DOM access, so the
rules for buttons, sticks and triggers are unit-testable in Node.

  button  : .pressed when pressed or value >= BUTTON_THRESHOLD
  stick   : slides axis * stickOffset px (0 inside the deadzone) and tilts
            rotateX(-y px)deg rotateY(x px)deg; .pressed on L3/R3
  trigger : "fade"  -> opacity = value
            "meter" -> opacity 1, clip-path inset from the top by (1 - value)
*/

import { leafParts } from './layout.js';

export const BUTTON_THRESHOLD = 0.25;

/** Normalise a Gamepad (or plain object of the same shape) into a snapshot. */
export function snapshot(pad) {
  if (!pad || pad.connected === false) return null;
  return {
    id: pad.id,
    index: pad.index,
    mapping: pad.mapping,
    buttons: Array.from(pad.buttons, (b) =>
      typeof b === 'object' ? { pressed: !!b.pressed, value: Number(b.value) || 0 }
                            : { pressed: b >= BUTTON_THRESHOLD, value: Number(b) || 0 }),
    axes: Array.from(pad.axes, (a) => Number(a) || 0),
  };
}

function buttonAt(snap, i) {
  return snap.buttons[i] || { pressed: false, value: 0 };
}

function round(v) {
  return Math.round(v * 100) / 100;
}

function stickState(snap, part, settings) {
  const [ix, iy] = part.axes;
  let x = snap.axes[ix] || 0;
  let y = snap.axes[iy] || 0;
  if (Math.hypot(x, y) < settings.deadzone) { x = 0; y = 0; }
  const dx = round(x * settings.stickOffset);
  const dy = round(y * settings.stickOffset);
  const btn = buttonAt(snap, part.button);
  return {
    pressed: btn.pressed || btn.value >= BUTTON_THRESHOLD,
    marginLeft: `${dx}px`,
    marginTop: `${dy}px`,
    transform: settings.tilt ? `rotateX(${round(-dy)}deg) rotateY(${dx}deg)` : '',
  };
}

function triggerState(snap, part, settings) {
  const v = Math.min(1, Math.max(0, buttonAt(snap, part.button).value));
  if (settings.triggerMode === 'meter') {
    return { opacity: '1', clipPath: `inset(${round((1 - v) * 100)}% 0 0 0)` };
  }
  return { opacity: String(round(v)), clipPath: '' };
}

/** Compute { connected, parts: { key: props } } for one frame. */
export function computeFrame(layout, snap, settings) {
  if (!snap) return { connected: false, parts: {} };
  const parts = {};
  for (const part of leafParts(layout)) {
    if (part.kind === 'stick') parts[part.key] = stickState(snap, part, settings);
    else if (part.kind === 'trigger') parts[part.key] = triggerState(snap, part, settings);
    else {
      const b = buttonAt(snap, part.button);
      parts[part.key] = { pressed: b.pressed || b.value >= BUTTON_THRESHOLD };
    }
  }
  return { connected: true, parts };
}
