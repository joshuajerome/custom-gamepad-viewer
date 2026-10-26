/* PlayStation 5 (DualSense) layout.

Describes the controller as data: the DOM tree the renderer builds, which
Standard Gamepad button/axis drives each part, and which theme image backs each
CSS variable. Class names match controller_css/layout.css (GPV's "ds4" markup),
so existing skins work unchanged. Adding a controller = adding a file like this.

Standard mapping reference: https://w3c.github.io/gamepad/#remapping
*/

export const ds5 = {
  id: 'ds5',
  name: 'PlayStation 5 (DualSense)',
  className: 'ds4',
  cssHref: 'css/layouts/ds5.css',
  width: 903,
  height: 713,

  // CSS variable -> theme image name (extension comes from the theme's format)
  assets: {
    base: 'Base',
    disconnected: 'Disconnected',
    trigger: 'Trigger',
    bumper: 'Bumper',
    touchpad: 'Touchpad',
    meta: 'Meta',
    start: 'Start',
    face: 'Face',
    stick: 'Stick',
    dpad: 'Dpad',
  },

  // kind: 'button' (toggles .pressed), 'trigger' (analog fill), 'stick' (moves + .pressed)
  parts: [
    { group: 'triggers', children: [
      { key: 'l2', className: 'trigger left', kind: 'trigger', button: 6 },
      { key: 'r2', className: 'trigger right', kind: 'trigger', button: 7 },
    ] },
    { group: 'bumpers', children: [
      { key: 'l1', className: 'bumper left', kind: 'button', button: 4 },
      { key: 'r1', className: 'bumper right', kind: 'button', button: 5 },
    ] },
    { key: 'touchpad', className: 'touchpad', kind: 'button', button: 17, tag: 'div' },
    { key: 'ps', className: 'meta', kind: 'button', button: 16, tag: 'div' },
    { group: 'arrows', children: [
      { key: 'create', className: 'back', kind: 'button', button: 8 },
      { key: 'options', className: 'start', kind: 'button', button: 9 },
    ] },
    { group: 'abxy', children: [
      { key: 'cross', className: 'button a', kind: 'button', button: 0 },
      { key: 'circle', className: 'button b', kind: 'button', button: 1 },
      { key: 'square', className: 'button x', kind: 'button', button: 2 },
      { key: 'triangle', className: 'button y', kind: 'button', button: 3 },
    ] },
    { group: 'sticks', children: [
      { key: 'ls', className: 'stick left', kind: 'stick', axes: [0, 1], button: 10 },
      { key: 'rs', className: 'stick right', kind: 'stick', axes: [2, 3], button: 11 },
    ] },
    { group: 'dpad', children: [
      { key: 'up', className: 'face up', kind: 'button', button: 12 },
      { key: 'down', className: 'face down', kind: 'button', button: 13 },
      { key: 'left', className: 'face left', kind: 'button', button: 14 },
      { key: 'right', className: 'face right', kind: 'button', button: 15 },
    ] },
  ],
};
