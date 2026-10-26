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
| `colors` | `region:hex` pairs for colourable themes, e.g. `shell:1e1e1e,accent:ff0055` | none |

Press a button once after the source loads; browsers hide gamepads until the first input.

### Offline file

Streamlabs and OBS **Local file** sources load over `file://`. There, browsers block ES modules
and `fetch()`, and the source can't take a query string. **Download overlay file** in the builder
gets around this by producing one self-contained HTML file (`js/standalone.js`):

- `js/bundle.js` (a ~100-line bundler for exactly the import/export forms used here) inlines the
  overlay's module graph into one classic script.
- The layout CSS is inlined.
- Theme images are inlined as `data:` URIs (SVG themes already recoloured).
- The settings query is baked into `window.CGV_STANDALONE`, which `js/overlay.js` reads instead of
  the URL.

Because it's assembled in the browser from the deployed files, there's no build step to keep in
sync.

## Themes and custom colours

`themes/index.json` lists the themes and their `format`:

- **`png`** (`white`, `black`): one PNG per layout asset (`Base.png`, `Face.png`, …). Drop in a
  folder with the same file names and add it to the index to create a new skin.
- **`svg`** (`dualsense`): one SVG per asset plus a `theme.json` that makes the theme colourable.
  The overlay fetches the SVGs, applies the `colors` overrides and inlines the result as data
  URIs. That keeps the art sharp at any scale, and nothing is generated on a server.

`theme.json` defines **regions** (shell, faceplate, accents, light bar, sticks, face buttons,
symbols, pressed highlight). For each region it lists the exact fill colours that region owns in
each SVG, plus an `anchor` (its main colour). A picked colour replaces the anchor. Every other
listed colour becomes a matching shade: it keeps its hue offset, saturation ratio and lightness
relative to the anchor, so shadows and highlights survive. A region with `"mode": "flat"` maps
all its colours to the picked one; the four PlayStation symbol colours work this way. `presets`
are named sets of overrides shown in the builder.

Authoring rules for colourable SVGs (tests in `tests/web/themes.test.js` enforce the first two):

- Every colour listed for a region must appear in that file.
- Presets may only use regions that exist.
- A colour that serves two purposes in one file needs to be split into two near-identical values
  first. In `Face.svg`, the pressed-state symbol ink is `#161616` and the idle button disc is
  `#171717`.

The `dualsense` SVGs are the original vector sources from `misc/svgs/` (commit `bf9d08f`), with
the D-pad and face-button artwork removed from `Base.svg`; the `Dpad` and `Face` sprites draw
those.

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
| `js/colors.js` | Pure region recolouring: hex/HSL, `shade`, `buildReplacements`, `recolorSvg` |
| `js/themes.js` | Theme index/definition loading; resolves a theme (+ colours) to CSS variables |
| `js/bundle.js`, `js/standalone.js` | Offline file: module bundler and self-contained HTML assembly |
| `themes/index.json` | Theme list shown in the builder (a test keeps it in sync with the folders) |
| `css/layouts/ds5.css` | Geometry from `controller_css/layout.css` plus structural rules GPV used to supply |
| `themes/white`, `themes/black` | PNG skins (copied from the repo's `themes/`) |
| `themes/dualsense` | Colourable SVG skin and its `theme.json` |

To add a controller, write `js/layouts/<name>.js` and `css/layouts/<name>.css`, then register
the layout in `js/layout.js`.
