"""Application entrypoint for Custom Gamepad Viewer.

Creates the FastAPI app, mounts static folders (/ui, /controller_css, /themes),
initializes persistent storage (FileStore) and in-memory state (AppState),
and includes all routers:
  - server/endpoints.py      → "/", "/healthz", "/favicon.ico"
  - server/api/config_routes → "/api/config", dynamic vars.css link targets
  - server/api/slot_routes   → "/api/slot"
  - server/api/themes_routes → "/api/themes"

Adds WsHub (WebSocket hub) for Phase 4 realtime sync. All API changes
(config/slot) will broadcast updates to connected clients.
"""

from __future__ import annotations
import os
from pathlib import Path
import signal
import sys
import threading
import time
import multiprocessing
from contextlib import suppress
import socket
import webbrowser
import urllib.request
import urllib.error
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from loguru import logger

from core.themes.validate import REQUIRED_FILES
from core.utils.resources import repo_root
from core.utils.user_dirs import data_dir, slot_file_path
from server.endpoints import get_router as core_router
from server.state import AppState, AppConfig
from server.storage.file_store import FileStore
from server.routes.config_routes import get_router as config_router
from server.routes.slot_routes import get_router as slot_router
from server.routes.themes_routes import get_router as themes_router
from server.services.theme_service import build_vars_css
from server.realtime.hub import WsHub
from server.routes.ws_routes import get_router as ws_router

# Paths
REPO_ROOT = repo_root()
UI_DIR = REPO_ROOT / "ui"
UI_PAGES = UI_DIR / "pages"
STATIC_SERVER_DIR = REPO_ROOT / "server" / "static"
CTRL_DIR = REPO_ROOT / "controller_css"
THEMES_DIR = REPO_ROOT / "themes"
DATA_DIR = data_dir()

INDEX_CSS_PATH = "controller_css/layout.css"      # static file served directly
VARS_CSS_HTTP = "/controller_css/vars.css"        # dynamic endpoint


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

_shutdown_callback: Optional[Callable[[], None]] = None

def register_shutdown_callback(callback: Callable[[], None] | None) -> None:
    global _shutdown_callback
    _shutdown_callback = callback

def trigger_shutdown_callback() -> None:
    cb = _shutdown_callback
    if cb:
        cb()

def _configure_logging() -> None:
    """Set up Loguru to log to stdout at INFO level."""
    logger.remove()
    logger.add(lambda m: print(m, end=""), level="INFO")


def _configure_cache_headers(app: FastAPI) -> None:
    """Attach middleware to disable browser caching (important for dev)."""
    @app.middleware("http")
    async def no_store_everything(request, call_next):
        resp = await call_next(request)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp


def _init_storage_and_state() -> tuple[FileStore, AppState]:
    """Create FileStore for persistence and initialize AppState from disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    slot_path = slot_file_path()
    config_path = DATA_DIR / "config.json"
    store = FileStore(slot_path=slot_path, config_path=config_path)

    persisted = store.read_config()
    init_skin = (persisted["skin"] if persisted else "white")

    slot = store.read_slot()
    init_player = slot["player"] or (persisted["player"] if persisted else 1)

    state = AppState(AppConfig(skin=init_skin, player=init_player))
    return store, state


def _mount_static(app: FastAPI) -> None:
    """Mount static folders: ui/, server/static/, themes/."""
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=False), name="ui")
    if STATIC_SERVER_DIR.exists():
        app.mount("/server/static", StaticFiles(directory=STATIC_SERVER_DIR, html=False), name="server-static")
    if THEMES_DIR.exists():
        app.mount("/themes", StaticFiles(directory=THEMES_DIR, html=False), name="themes")


def _mount_controller_css(app: FastAPI, state: AppState) -> None:
    """Mount controller_css/, with vars.css served dynamically."""
    ctrl_app = FastAPI()

    @ctrl_app.get("/vars.css", include_in_schema=False)
    async def dynamic_vars_css():
        cfg = state.get()
        skin_folder_rel = f"themes/{cfg.skin}"
        css_bytes = build_vars_css(skin_folder_rel, REQUIRED_FILES)
        return Response(content=css_bytes, media_type="text/css; charset=utf-8")

    ctrl_app.mount("/", StaticFiles(directory=CTRL_DIR, html=False), name="ctrl-static")
    app.mount("/controller_css", ctrl_app)


def _include_routers(app: FastAPI, state: AppState, store: FileStore, hub: WsHub) -> None:
    """Attach all API routers with injected dependencies."""
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))

    app.include_router(core_router(UI_PAGES))
    app.include_router(config_router(state=state, storage=store, host=host, port=port, index_css_path=INDEX_CSS_PATH, hub=hub))
    app.include_router(slot_router(state=state, storage=store, hub=hub))
    app.include_router(themes_router())
    app.include_router(ws_router(hub=hub))


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #

def create_app() -> FastAPI:
    """Factory: assemble and return the FastAPI application."""
    _configure_logging()
    app = FastAPI(title="Local Gamepad Viewer (Phase 4)")

    _configure_cache_headers(app)
    store, state = _init_storage_and_state()
    hub = WsHub()  # shared across routers
    _mount_static(app)
    _mount_controller_css(app, state)
    _include_routers(app, state, store, hub)

    if getattr(sys, "frozen", False):
        @app.post("/__internal/shutdown", include_in_schema=False)
        async def _shutdown_endpoint():
            trigger_shutdown_callback()
            return {"status": "shutting_down"}

    return app


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))

    reload_env = os.getenv("APP_RELOAD")
    if reload_env is None:
        reload_flag = not getattr(sys, "frozen", False)
    else:
        reload_flag = reload_env.lower() in {"1", "true", "yes", "on"}

    mode = "dev (reload enabled)" if reload_flag else "packaged/prod (reload disabled)"
    logger.info(f"Starting server on http://{host}:{port} [{mode}]")

    if reload_flag:
        uvicorn.run(
            "app:create_app",
            host=host,
            port=port,
            factory=True,
            reload=True,
        )
    else:
        def _run_packaged_server() -> int:
            multiprocessing.freeze_support()

            auto_open = os.getenv("APP_OPEN_BROWSER", "1").lower() in {"1", "true", "yes", "on"}

            def _open_browser() -> None:
                with suppress(Exception):
                    webbrowser.open(f"http://{host}:{port}")

            def _server_already_running() -> bool:
                try:
                    with socket.create_connection((host, port), timeout=0.6):
                        return True
                except OSError:
                    return False

            def _request_existing_shutdown() -> bool:
                try:
                    req = urllib.request.Request(
                        url=f"http://{host}:{port}/__internal/shutdown",
                        method="POST",
                        data=b"{}",
                        headers={"Content-Type": "application/json"},
                    )
                    urllib.request.urlopen(req, timeout=1.0)
                    return True
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError, OSError):
                    return False

            def _wait_for_port_close(timeout: float = 5.0) -> bool:
                deadline = time.perf_counter() + timeout
                while time.perf_counter() < deadline:
                    if not _server_already_running():
                        return True
                    time.sleep(0.1)
                return not _server_already_running()

            if _server_already_running():
                logger.info("Detected existing Custom Gamepad Viewer server; requesting restart.")
                requested_shutdown = _request_existing_shutdown()
                if requested_shutdown:
                    logger.info("Requested existing server shutdown; waiting for port to become available...")
                    if not _wait_for_port_close(timeout=10.0):
                        logger.error("Existing server did not shut down in time; aborting launch.")
                        return 1
                else:
                    logger.warning("Existing server not responsive to shutdown request; aborting new launch.")
                    return 1

            app_instance = create_app()
            config = uvicorn.Config(
                app=app_instance,
                host=host,
                port=port,
                log_level="info",
                reload=False,
                factory=False,
            )
            server = uvicorn.Server(config)
            stop_event = threading.Event()

            def _server_target() -> None:
                try:
                    server.run()
                finally:
                    stop_event.set()

            def _request_stop() -> None:
                server.should_exit = True
                stop_event.set()

            register_shutdown_callback(_request_stop)

            server_thread = threading.Thread(target=_server_target, name="uvicorn-server", daemon=True)
            server_thread.start()

            start_deadline = time.perf_counter() + 10
            while not server.started and server_thread.is_alive() and time.perf_counter() < start_deadline:
                time.sleep(0.1)

            if not server.started:
                if server_thread.is_alive():
                    logger.error("Uvicorn failed to start within timeout; exiting.")
                else:
                    logger.error("Uvicorn thread terminated before startup; exiting.")
                register_shutdown_callback(None)
                return 1

            def _signal_handler(signum, frame):
                logger.info(f"Received signal {signum}; shutting down server...")
                server.should_exit = True
                stop_event.set()

            for sig in (signal.SIGINT, signal.SIGTERM):
                with suppress(ValueError):
                    signal.signal(sig, _signal_handler)

            def _launch_control_window() -> bool:
                try:
                    import tkinter as tk  # type: ignore
                except Exception as exc:  # pragma: no cover - environment without Tk
                    logger.warning("tkinter unavailable (%s); running headless.", exc)
                    return False

                shutdown_initiated = False

                def _trigger_shutdown() -> None:
                    nonlocal shutdown_initiated
                    if not shutdown_initiated:
                        shutdown_initiated = True
                        _request_stop()

                root = tk.Tk()
                root.title("Custom Gamepad Viewer")
                root.geometry("380x180")
                root.resizable(False, False)

                label = tk.Label(
                    root,
                    text="Custom Gamepad Viewer is running.\n"
                    "Use Open Viewer to relaunch the browser.\n"
                    "Close this window or Quit Server to stop.",
                    justify="center",
                    padx=12,
                    pady=12,
                )
                label.pack()

                button_frame = tk.Frame(root, padx=12, pady=8)
                button_frame.pack(padx=12, pady=8)

                open_btn = tk.Button(button_frame, text="Open Viewer", width=16, command=_open_browser)
                open_btn.grid(row=0, column=0, padx=6)

                def _quit_action() -> None:
                    _trigger_shutdown()
                    root.quit()

                quit_btn = tk.Button(button_frame, text="Quit Server", width=16, command=_quit_action)
                quit_btn.grid(row=0, column=1, padx=(6, 12))

                root.protocol("WM_DELETE_WINDOW", _quit_action)

                if auto_open:
                    root.after(200, _open_browser)

                def _poll_stop() -> None:
                    if stop_event.is_set():
                        with suppress(Exception):
                            root.quit()
                        return
                    root.after(250, _poll_stop)

                root.after(250, _poll_stop)

                try:
                    root.mainloop()
                finally:
                    _trigger_shutdown()

                return True

            gui_started = _launch_control_window()

            if not gui_started:
                if auto_open:
                    _open_browser()
                try:
                    while not stop_event.is_set():
                        time.sleep(0.25)
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received; shutting down.")
                    _request_stop()

            server_thread.join(timeout=5)
            register_shutdown_callback(None)
            return 0

        exit_code = _run_packaged_server()
        sys.exit(exit_code)
