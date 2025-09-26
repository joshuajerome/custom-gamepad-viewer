"""Application entrypoint for Local Gamepad Viewer.

This module builds a FastAPI app that:
- Initializes persistent storage (FileStore) and in-memory state (AppState).
- Mounts static folders: /ui (HTML/JS/CSS), /themes (PNG assets).
- Exposes page routes: "/", "/healthz", "/favicon.ico" via server/endpoints.py.
- Exposes JSON APIs:
    • /api/config  (get/set skin & player; returns preview URLs)
    • /api/slot    (get/set active gamepad index ⇒ player)
    • /api/themes  (list discovered themes with validation status)
- Serves a dynamic /controller_css/vars.css (selected-skin CSS variables) and
  a static /controller_css/layout.css (controller layout CSS) via a sub-app.
- Disables HTTP caching in dev to avoid stale UI between localhost/127.0.0.1.

Run locally:
    uv run python app.py
or:
    source .venv/bin/activate && python app.py
"""

from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from loguru import logger

from core.themes.validate import REQUIRED_FILES
from core.utils.resources import repo_root
from core.utils.user_dirs import data_dir, slot_file_path
from server.endpoints import get_router as core_router
from server.state import AppState, AppConfig
from server.storage.file_store import FileStore
from server.api.config_routes import get_router as config_router
from server.api.slot_routes import get_router as slot_router
from server.api.themes_routes import get_router as themes_router
from server.services.theme_service import build_vars_css


# ---- Path resolution (module-level constants) --------------------------------
REPO_ROOT = repo_root()
UI_DIR = REPO_ROOT / "ui"
UI_PAGES = UI_DIR / "pages"
STATIC_SERVER_DIR = REPO_ROOT / "server" / "static"
CTRL_DIR = REPO_ROOT / "controller_css"
THEMES_DIR = REPO_ROOT / "themes"
DATA_DIR = data_dir()

INDEX_CSS_PATH = "controller_css/layout.css"  # static CSS file path used in URLs

def _configure_logging() -> None:
    """Install a concise console logger for development."""
    logger.remove()
    logger.add(lambda m: print(m, end=""), level="INFO")

def _configure_cache_headers(app: FastAPI) -> None:
    """Attach middleware that disables HTTP caching (prevents stale assets during dev)."""
    @app.middleware("http")
    async def no_store_everything(request, call_next):
        resp = await call_next(request)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp

def _init_storage_and_state() -> tuple[FileStore, AppState]:
    """Create the JSON-backed storage and initialize in-memory state (skin/player)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    store = FileStore(
        slot_path=slot_file_path(),
        config_path=DATA_DIR / "config.json",
    )

    persisted = store.read_config()
    init_skin = persisted["skin"] if persisted else "white"

    slot = store.read_slot()
    init_player = slot["player"] or (persisted["player"] if persisted else 1)

    state = AppState(AppConfig(skin=init_skin, player=init_player))
    return store, state

def _mount_static(app: FastAPI) -> None:
    """Mount static directories for UI, themes, and (optionally) server/static."""
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=False), name="ui")
    if STATIC_SERVER_DIR.exists():
        app.mount("/server/static", StaticFiles(directory=STATIC_SERVER_DIR, html=False), name="server-static")
    if THEMES_DIR.exists():
        app.mount("/themes", StaticFiles(directory=THEMES_DIR, html=False), name="themes")

def _mount_controller_css(app: FastAPI, state: AppState) -> None:
    """Mount a sub-app at /controller_css with dynamic vars.css and static layout.css."""
    ctrl_app = FastAPI()

    @ctrl_app.get("/vars.css", include_in_schema=False)
    async def dynamic_vars_css():
        cfg = state.get()
        skin_folder_rel = f"themes/{cfg.skin}"  # resolved by the browser against app root
        css_bytes = build_vars_css(skin_folder_rel, REQUIRED_FILES)
        return Response(content=css_bytes, media_type="text/css; charset=utf-8")

    # Serve other CSS files (e.g., layout.css) from the same folder
    ctrl_app.mount("/", StaticFiles(directory=CTRL_DIR, html=False), name="ctrl-static")

    # Important: mount the sub-app, not a plain StaticFiles, so /vars.css resolves here
    app.mount("/controller_css", ctrl_app)

def _include_routers(app: FastAPI, state: AppState, store: FileStore) -> None:
    """Register page and API routers and provide config for URL generation."""
    app.include_router(core_router(UI_PAGES))

    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))

    app.include_router(
        config_router(
            state=state,
            storage=store,
            host=host,
            port=port,
            index_css_path=INDEX_CSS_PATH,
        )
    )
    app.include_router(slot_router(state=state, storage=store))
    app.include_router(themes_router())

def create_app() -> FastAPI:
    """Factory: assemble and return the FastAPI application."""
    _configure_logging()
    app = FastAPI(title="Local Gamepad Viewer (Phase 3)")

    _configure_cache_headers(app)
    store, state = _init_storage_and_state()
    _mount_static(app)
    _mount_controller_css(app, state)
    _include_routers(app, state, store)

    return app

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    logger.info(f"Starting dev server on http://{host}:{port}")
    uvicorn.run("app:create_app", host=host, port=port, factory=True, reload=True)
