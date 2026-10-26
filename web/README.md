# Web overlay (static)

A static version of Custom Gamepad Viewer that reads the controller itself with the browser
Gamepad API. It needs no server, no install, and no gamepadviewer.com. It's meant to be hosted
on GitHub Pages and used directly as a Streamlabs / OBS Browser Source.

## Use

Open `index.html` (the builder). Pick a theme, player slot and display options, check the live
preview, then **Copy** the browser-source URL. The builder detects your controller's slot when you
press a button, and remembers your choices in this browser. To edit an existing URL, open the
builder with the same query, e.g. `index.html?theme=black&p=2`.

The overlay URL looks like:

```
overlay.html?theme=white&p=1
```

| Param | Values | Default |
|---|---|---|
| `theme` | folder name under `themes/` | `white` |
| `p` | player slot 1–4 | `1` |
| `scale` | `fit` or a number (e.g. `0.5`) | `fit` |
| `dz` | stick deadzone 0–0.9 | `0.25` |
| `offset` | max stick travel, px | `22` |
| `tilt` | `0` disables stick tilt | `1` |
| `trigger` | `fade` (opacity) or `meter` (fills from the bottom) | `fade` |
| `debug` | `1` shows raw controller input | `0` |

Press a button once after the source loads; browsers hide gamepads until the first input.

## Hosting

Live at **https://joshuajerome.github.io/custom-gamepad-viewer/**. For example:

```
https://joshuajerome.github.io/custom-gamepad-viewer/overlay.html?theme=white&p=1
```

`.github/workflows/web-pages.yml` runs `npm run test:web` on PRs that touch `web/`. When `web/`
changes on `main` or a `rel/web-*` branch, it also publishes the `web/` folder as-is (no build
step). The `github-pages` environment only accepts deploys from those branches.

## Develop

```bash
npm run serve:web     # http://127.0.0.1:8765/ (zero-dependency Node static server)
npm run test:web      # node --test, no installs needed
```

## Structure

| Path | Role |
|---|---|
| `js/layouts/ds5.js` | Controller described as data: DOM parts, Standard Gamepad button/axis per part, theme assets |
| `js/layout.js` | Layout registry, `leafParts`, `themeVars` |
| `js/settings.js` | URL query → settings (validated, clamped) |
| `js/frame.js` | Pure gamepad snapshot → per-part visual state (pressed, stick offset/tilt, trigger fill) |
| `js/renderer.js` | Builds the DOM from a layout and applies frames (only changed values) |
| `js/overlay.js` | Entry point and `requestAnimationFrame` loop |
| `js/builder.js`, `css/builder.css` | Builder page: form ↔ settings ↔ URL, live preview iframe, slot detection |
| `themes/index.json` | Theme list shown in the builder (a test keeps it in sync with the folders) |
| `css/layouts/ds5.css` | Geometry from `controller_css/layout.css` plus structural rules GPV used to supply |
| `themes/` | Skin PNGs (copied from the repo's `themes/`) |

To add a controller, write `js/layouts/<name>.js` and `css/layouts/<name>.css`, then register
the layout in `js/layout.js`.
