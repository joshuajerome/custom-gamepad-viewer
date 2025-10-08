"""Application entrypoint.

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

    return app


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    logger.info(f"Starting dev server on http://{host}:{port}")
    uvicorn.run("app:create_app", host=host, port=port, factory=True, reload=True)
