/* DOM renderer.

Builds the controller markup from a layout definition and applies frames
produced by computeFrame(). Only touches the DOM when a value changes, so the
per-frame cost stays tiny inside a browser source.
*/

import { leafParts, themeVars } from './layout.js';

const STYLE_PROPS = ['opacity', 'clipPath', 'marginLeft', 'marginTop', 'transform'];

export class ControllerRenderer {
  constructor(layout, mount) {
    this.layout = layout;
    this.root = document.createElement('div');
    this.root.className = `controller ${layout.className} disconnected`;
    this.els = {};
    this.last = {};
    this.connected = false;

    for (const part of layout.parts) {
      if (part.group) {
        const g = document.createElement('div');
        g.className = part.group;
        for (const child of part.children) g.appendChild(this.#makePart(child));
        this.root.appendChild(g);
      } else {
        this.root.appendChild(this.#makePart(part));
      }
    }
    mount.appendChild(this.root);
  }

  #makePart(part) {
    const el = document.createElement(part.tag || 'span');
    el.className = part.className;
    el.dataset.part = part.key;
    this.els[part.key] = el;
    this.last[part.key] = {};
    return el;
  }

  setTheme(themeBaseUrl) {
    // url() inside a custom property resolves against the stylesheet that uses it
    // (css/layouts/), so hand the layout CSS absolute URLs.
    const absolute = new URL(`${themeBaseUrl.replace(/\/+$/, '')}/`, document.baseURI).href;
    for (const [name, value] of Object.entries(themeVars(this.layout, absolute))) {
      this.root.style.setProperty(name, value);
    }
  }

  render(frame) {
    if (frame.connected !== this.connected) {
      this.connected = frame.connected;
      this.root.classList.toggle('disconnected', !frame.connected);
    }
    if (!frame.connected) return;

    for (const part of leafParts(this.layout)) {
      const next = frame.parts[part.key];
      if (!next) continue;
      const el = this.els[part.key];
      const prev = this.last[part.key];

      if (next.pressed !== prev.pressed) el.classList.toggle('pressed', !!next.pressed);
      for (const prop of STYLE_PROPS) {
        if (prop in next && next[prop] !== prev[prop]) el.style[prop] = next[prop];
      }
      this.last[part.key] = next;
    }
  }
}
