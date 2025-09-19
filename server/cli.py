# server/cli.py
from http.server import ThreadingHTTPServer
from loguru import logger
import argparse
from pathlib import Path

from server.config import Config
from server.logsink import setup_logging
from server.slot_store import SlotStore
from server.handler import DevHandler
from server.state import AppState, AppStateData

def resolve_player_slot(p_arg, store: SlotStore) -> int:
    if isinstance(p_arg, int):
        return p_arg if 1 <= p_arg <= 4 else 1
    if isinstance(p_arg, str) and p_arg.isdigit():
        n = int(p_arg)
        return n if 1 <= n <= 4 else 1
    # auto
    player = store.read_player()
    if player:
        logger.info("Auto slot: using saved player p={}", player)
        return player
    logger.info("Auto slot: no saved slot; defaulting to p=1")
    return 1

def main():
    cfg = Config()

    ap = argparse.ArgumentParser(description="Serve Gamepad Viewer assets with skin toggle and slot autosave.")
    ap.add_argument("--host", default=cfg.host, help=f"bind address (default: {cfg.host})")
    ap.add_argument("--port", type=int, default=cfg.port, help=f"port (default: {cfg.port})")
    ap.add_argument("--skin", choices=cfg.skin_folders.keys(), default="white",
                    help="image set to expose via /css/vars.css (white|black)")
    ap.add_argument("--p", default="auto",
                    help="Gamepad Viewer player slot (1-4) or 'auto' to use last saved slot.json")
    ap.add_argument("--index", default=cfg.index_css_path,
                    help=f"path to main CSS relative to server root (default: {cfg.index_css_path})")
    ap.add_argument("--vars", default=cfg.vars_css_path,
                    help=f"path for generated vars CSS (default: {cfg.vars_css_path})")
    ap.add_argument("--slotfile", default=cfg.slot_json_path,
                    help=f"path to slot.json (default: {cfg.slot_json_path})")
    ap.add_argument("--log-level", default="INFO", help="loguru level (DEBUG, INFO, WARNING, ERROR)")
    args = ap.parse_args()

    setup_logging(args.log_level)

    if not Path(args.index).exists():
        logger.error("layout.css not found at {}", args.index)
    for name, folder in cfg.skin_folders.items():
        if not Path(folder).exists():
            logger.error("Skin folder '{}' missing at {}", name, folder)

    store = SlotStore(args.slotfile)
    player = resolve_player_slot(args.p, store)

    # App state (live)
    state = AppState(AppStateData(skin=args.skin, player=player))

    # Wire handler
    DevHandler.index_css_path = args.index
    DevHandler.vars_css_path  = args.vars
    DevHandler.skin_folders   = cfg.skin_folders
    DevHandler.var_files      = cfg.var_files
    DevHandler.slot_store     = store
    DevHandler.state          = state
    DevHandler.host           = args.host
    DevHandler.port           = args.port

    # Start server
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
        logger.info("Slot checker:      http://{}:{}/server/static/check_slot.html", sa_host, sa_port)
        logger.info("Config API:        GET/POST http://{}:{}/api/config", sa_host, sa_port)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt; shutting down…")
        finally:
            httpd.server_close()
