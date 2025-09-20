# server/cli.py
from http.server import ThreadingHTTPServer
from loguru import logger
import argparse
import sys
import os
from pathlib import Path

from server.config import Config
from server.logsink import setup_logging
from server.slot_store import SlotStore
from server.handler import DevHandler
from server.state import AppState, AppStateData

def _default_slot_path() -> Path:
    # Cross-platform user data dir
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "LocalGamepadViewer" / "slot.json"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "LocalGamepadViewer"
        return base / "slot.json"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return base / "local-gamepad-viewer" / "slot.json"

def resolve_player_slot(p_arg, store: SlotStore) -> int:
    if isinstance(p_arg, int):
        return p_arg if 1 <= p_arg <= 4 else 1
    if isinstance(p_arg, str) and p_arg.isdigit():
        n = int(p_arg); return n if 1 <= n <= 4 else 1
    player = store.read_player()
    if player:
        logger.info("Auto slot: using saved player p={}", player)
        return player
    logger.info("Auto slot: no saved slot; defaulting to p=1")
    return 1

def main():
    cfg = Config()

    ap = argparse.ArgumentParser(description="Serve Gamepad Viewer assets with skin toggle and slot autosave.")
    ap.add_argument("--host", default=cfg.host)
    ap.add_argument("--port", type=int, default=cfg.port)
    ap.add_argument("--skin", choices=cfg.skin_folders.keys(), default="white")
    ap.add_argument("--p", default="auto", help="1-4 or 'auto'")
    ap.add_argument("--index", default=cfg.index_css_path)
    ap.add_argument("--vars", default=cfg.vars_css_path)
    # NEW: default to user data dir instead of tmp/slot.json
    ap.add_argument("--slotfile", default=str(_default_slot_path()))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()

    setup_logging(args.log_level)

    # Ensure slotfile directory exists
    slot_path = Path(args.slotfile)
    slot_path.parent.mkdir(parents=True, exist_ok=True)

    if not Path(args.index).exists():
        logger.error("layout.css not found at {}", args.index)
    for name, folder in cfg.skin_folders.items():
        if not Path(folder).exists():
            logger.error("Skin folder '{}' missing at {}", name, folder)

    store = SlotStore(str(slot_path))
    player = resolve_player_slot(args.p, store)

    state = AppState(AppStateData(skin=args.skin, player=player))

    DevHandler.index_css_path = args.index
    DevHandler.vars_css_path  = args.vars
    DevHandler.skin_folders   = cfg.skin_folders
    DevHandler.var_files      = cfg.var_files
    DevHandler.slot_store     = store
    DevHandler.state          = state
    DevHandler.host           = args.host
    DevHandler.port           = args.port

    ThreadingHTTPServer.allow_reuse_address = True
    server_address = (args.host, args.port)
    with ThreadingHTTPServer(server_address, DevHandler) as httpd:
        sa_host, sa_port = httpd.socket.getsockname()

        css_url = f"http://{sa_host}:{sa_port}/{args.index}"
        gpv_url = f"https://gamepadviewer.com/?p={player}&s=5&editcss={css_url}"

        logger.info("HTTP server started on http://{}:{}", sa_host, sa_port)
        logger.info("Initial skin: {}", state.get().skin)
        logger.info("Serving layout.css: {}", css_url)
        logger.info("Generated vars.css: http://{}:{}/{}", sa_host, sa_port, args.vars)
        logger.info("Gamepad Viewer link: {}", gpv_url)
        logger.info("Home:              http://{}:{}/", sa_host, sa_port)
        logger.info("Overlay (no UI):   http://{}:{}/overlay", sa_host, sa_port)
        logger.info("Slot file:         {}", slot_path)
        logger.info("Slot checker:      http://{}:{}/server/static/check_slot.html", sa_host, sa_port)
        logger.info("Config API:        GET/POST http://{}:{}/api/config", sa_host, sa_port)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt; shutting down…")
        finally:
            httpd.server_close()
