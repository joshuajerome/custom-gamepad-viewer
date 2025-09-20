from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from loguru import logger
import json

from server.theme import build_vars_css
from server.slot_store import SlotStore
from server.state import AppState

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[1]
STATIC_DIR = BASE_DIR / "static"

class DevHandler(SimpleHTTPRequestHandler):
    index_css_path: str = "controller_css/layout.css"
    vars_css_path:  str = "controller_css/vars.css"
    skin_folders:   dict = {}
    var_files:      dict = {}
    slot_store:     SlotStore = None
    state:          AppState = None
    host: str = "127.0.0.1"
    port: int = 8000

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" + self.vars_css_path:
            return self._serve_vars_css()
        if parsed.path == "/api/slot":
            return self._serve_slot_json()
        if parsed.path == "/api/config":
            return self._serve_config_json()
        if parsed.path == "/api/themes":
            return self._serve_themes()
        if parsed.path == "/overlay":
            return self._serve_overlay()
        return super().do_GET()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/slot":
            return self._handle_slot_post()
        if parsed.path == "/api/config":
            return self._handle_config_post()
        self.send_error(404, "Not Found")

    # -------- helpers

    def _gpv_url(self, player: int) -> str:
        css_url = f"http://{self.host}:{self.port}/{self.index_css_path}"
        return f"https://gamepadviewer.com/?p={player}&s=5&editcss={css_url}"

    def _serve_themes(self):
        """Return discovered themes and any missing files per theme."""
        payload = {"themes": []}
        for name, relpath in sorted(self.skin_folders.items()):
            folder = REPO_ROOT / relpath
            missing = [f for f in self.var_files.values() if not (folder / f).exists()]
            payload["themes"].append({
                "name": name,
                "path": relpath,
                "ok": len(missing) == 0,
                "missing": missing,
            })
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_vars_css(self):
        skin = self.state.get().skin
        if skin not in self.skin_folders:
            if self.skin_folders:
                skin = sorted(self.skin_folders.keys())[0]
                self.state.set_skin(skin)
                logger.warning("Requested skin not found; falling back to '{}'", skin)
            else:
                self.send_error(500, "No themes found in /themes")
                return

        skin_folder = self.skin_folders[skin]
        css = build_vars_css(skin_folder, self.var_files)
        logger.debug("Serving /{} (skin='{}')", self.vars_css_path, skin)
        self.send_response(200)
        self.send_header("Content-Type", "text/css; charset=utf-8")
        self.send_header("Content-Length", str(len(css)))
        self.end_headers()
        self.wfile.write(css)

    def _serve_slot_json(self):
        data = self.slot_store.read_raw()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_config_json(self):
        cfg = self.state.get()
        payload = {
            "skin": cfg.skin,
            "player": cfg.player,
            "available_skins": sorted(self.skin_folders.keys()),
            "gpv_url": self._gpv_url(cfg.player),
            "css_url": f"http://{self.host}:{self.port}/{self.index_css_path}",
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_config_post(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self.send_error(400, "Invalid JSON")
            return

        if "skin" in data:
            skin = data["skin"]
            if skin in self.skin_folders:
                self.state.set_skin(skin)
                logger.info("Skin changed -> {}", skin)
            else:
                self.send_error(400, f"Unknown skin '{skin}'")
                return

        if "player" in data:
            try:
                self.state.set_player(int(data["player"]))
                logger.info("Player changed -> p={}", int(data["player"]))
            except Exception:
                pass

        cfg = self.state.get()
        payload = {
            "ok": True,
            "skin": cfg.skin,
            "player": cfg.player,
            "gpv_url": self._gpv_url(cfg.player),
            "css_url": f"http://{self.host}:{self.port}/{self.index_css_path}",
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_slot_post(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            index = int(data["index"])
            if index < 0:
                raise ValueError()
        except Exception:
            self.send_error(400, "Expected JSON {\"index\": <non-negative int>}")
            return

        try:
            player, payload_bytes = self.slot_store.save_index(index)
        except Exception as e:
            self.send_error(500, f"Persist failed: {e}")
            return

        self.state.set_player(player)
        logger.info("Updated player from slot POST -> p={}", player)

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload_bytes)))
        self.end_headers()
        self.wfile.write(payload_bytes)

        logger.info("Updated Gamepad Viewer link: {}", self._gpv_url(player))

    def _serve_overlay(self):
        path = STATIC_DIR / "overlay.html"
        if not path.exists():
            logger.error(f"Expected overlay.html path: {path}")
            self.send_error(404, "overlay.html not found")
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

