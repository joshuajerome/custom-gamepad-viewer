# Custom Gamepad Viewer

Show your controller on stream with **your own skin and colours**. Add it to Streamlabs or OBS as a
**Browser Source**. Nothing to install.

**→ Open the builder: https://joshuajerome.github.io/custom-gamepad-viewer/**

It's inspired by [gamepadviewer.com](https://gamepadviewer.com) (GPV), but it reads the controller
itself, so you get custom colours, live preview and an offline file. You don't need to host
stylesheets anywhere. It currently supports the PlayStation 5 (DualSense) layout.

---

## Quick start (Streamlabs / OBS)

1. Open the **builder** link above and press a button on your controller. The builder detects
   which player slot it's in.
2. Pick a **theme**. *DualSense (custom colours)* lets you recolour the shell, faceplate,
   accents, light bar, sticks, face buttons, symbols and the pressed highlight. Start from a
   preset or pick each colour yourself.
3. Adjust the display options if you like: trigger style, size, stick deadzone, travel and tilt.
   The preview shows exactly what the stream will show.
4. Click **Copy**. In Streamlabs or OBS, choose **Add Source → Browser Source**, paste the URL, and
   set the width and height the builder shows (903 × 713 at full size).
5. Press a controller button once after the source loads. Browsers hide controllers until they
   see an input.

**Offline:** click **Download overlay file** to get one HTML file with your settings built in. In
the Browser Source, tick **Local file** and select it. It needs no internet and doesn't depend on
this website. Download it again whenever you change settings.

**Wrong buttons or nothing moving?** Open the overlay with `&debug=1` (the builder links to this).
It shows which controller slot is used, its `mapping` (it should say `standard`), and the raw
button and stick values.

---

## How it works

```
Controller ─► browser Gamepad API ─► frame.js (input → visual state) ─► renderer.js (DOM)
                                                                          │
                     theme images (PNG, or SVG recoloured in the browser) ┘ via CSS variables
```

The overlay polls the controller every animation frame. Each part of the controller is an HTML
element, styled by a layout stylesheet and backed by a theme image:

| Part | Input | What you see |
|---|---|---|
| **Face buttons, D-pad, L3/R3** | pressed / not pressed | Each image is a **sprite sheet**: the top row is idle, the bottom row is pressed. Pressing adds `.pressed`, which shifts the image up one row. |
| **Bumpers, Create/Options, PS, touchpad** | pressed / not pressed | The highlight image is hidden and appears while pressed. |
| **Sticks** | X/Y axes (−1 to 1) | The stick cap **slides** `axis × 22px` (configurable) from centre and tilts slightly in the push direction. Inside the deadzone (default 0.25) it stays centred. |
| **Triggers (L2/R2)** | analog 0 to 1 | **Fade**: the pressed image fades in with pressure (50% squeeze = 50% opacity). **Fill meter**: it fills from the bottom instead. |
| **No controller** | none | The whole controller swaps to the *Disconnected* image. |

**Custom colours** come from vector (SVG) art. Each theme's `theme.json` lists which exact
colours belong to each region. When you pick a colour, the overlay rewrites those colours as
shades of your pick (keeping each part's light and shadow), then hands the result to the page as
inline images. All of this happens in the browser; there's no server. Details and theme-authoring
rules are in [`web/README.md`](web/README.md).

### Compared with gamepadviewer.com

| | gamepadviewer.com | Custom Gamepad Viewer |
|---|---|---|
| Layouts | Xbox, PS3/PS4, GameCube, Switch, fight stick, … | PS5 / DualSense (more can be added as data files) |
| Custom skins | Host your own CSS and images, paste an `editcss=` URL | Built-in themes; drop-in PNG themes; colour pickers |
| Custom colours | Edit images by hand | Per-region pickers and presets |
| Setup | Edit URL parameters by hand | Builder with live preview and slot detection |
| Options | `sc`, `op`, `dz`, `smeter`, `soffset`, `nocurve`, `map`, … | Size, deadzone, trigger meter, stick travel, tilt (no opacity or remapping yet) |
| Offline | No | Yes: single downloaded HTML file |
| Ads / third-party scripts | Yes | No |

---

## Repository layout

| Path | What it is |
|---|---|
| `web/` | **The web overlay and builder** (static, hosted on GitHub Pages). See [`web/README.md`](web/README.md). |
| `tests/web/` | Its tests: `node --test`, nothing to install |
| `app.py`, `server/`, `core/`, `ui/`, `controller_css/`, `themes/` | The original **desktop app** (below) |
| `tests/core/` | Desktop app tests (pytest) |

### Develop the web overlay

Requires Node 22+ and no `npm install`.

```bash
npm run serve:web   # http://127.0.0.1:8765/
npm run test:web
```

Pushes to `main` or `rel/web-*` that touch `web/` run the tests and deploy to GitHub Pages
(`.github/workflows/web-pages.yml`).

---

## Desktop app (original)

The first version of this project is a Python (FastAPI) app that runs on your PC. It hosts skin
images and a stylesheet locally, and embeds **gamepadviewer.com** with
`?editcss=http://127.0.0.1:8000/controller_css/layout.css`. GPV reads the controller; the local
CSS and PNGs decide how it looks. Use `http://127.0.0.1:8000/ui/pages/overlay.html` as the
browser source; it reloads when you change theme or player in the control panel at
`http://127.0.0.1:8000`. Windows and macOS builds come from `.github/workflows/build-binaries.yml`.

```bash
# Windows
powershell -File .\scripts\setup.ps1 -build
# macOS / Linux
./scripts/setup.sh --build

uv run python app.py      # dev server with reload on http://127.0.0.1:8000
uv run pytest
uv run ruff check && uv run mypy .
scripts\build-exe.ps1 -Clean -OneFile   # Windows EXE
```

Settings are stored in `%LOCALAPPDATA%\Custom Gamepad Viewer\` (Windows),
`~/Library/Application Support/Custom Gamepad Viewer/` (macOS), or
`~/.local/share/local-gamepad-viewer/` (Linux).

Known limitations of the desktop app:
- It needs internet, because GPV still loads remotely.
- If port 8000 is taken by another program, the packaged app exits.
- Themes in the per-user folder are listed but not served.

The web overlay avoids all three.

See [`AGENTS.md`](AGENTS.md) for contributor conventions.
