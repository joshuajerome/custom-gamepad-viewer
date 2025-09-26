"""Application entrypoint.

Creates the FastAPI app, mounts static folders (/ui, /controller_css, /themes),
initializes persistent storage (FileStore) and in-memory state (AppState),
and includes all routers:
  - server/endpoints.py      → "/", "/healthz", "/favicon.ico"
  - server/api/config_routes → "/api/config", dynamic vars.css link targets
  - server/api/slot_routes   → "/api/slot"
  - server/api/themes_routes → "/api/themes"

Also exposes /controller_css/vars.css dynamically, so the active skin updates
CSS URLs without editing files. Run locally via: `python app.py`.
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
from server.api.config_routes import get_router as config_router
from server.api.slot_routes import get_router as slot_router
from server.api.themes_routes import get_router as themes_router
from server.services.url import build_gpv_url
from server.services.theme import build_vars_css

# Paths
REPO_ROOT = repo_root()
UI_DIR = REPO_ROOT / "ui"
UI_PAGES = UI_DIR / "pages"
STATIC_SERVER_DIR = REPO_ROOT / "server" / "static"
CTRL_DIR = REPO_ROOT / "controller_css"
THEMES_DIR = REPO_ROOT / "themes"
DATA_DIR = data_dir()

INDEX_CSS_PATH = "controller_css/layout.css"      # static file served directly
VARS_CSS_HTTP = "/controller_css/vars.css"        # dynamic endpoint (below)

def create_app() -> FastAPI:
    app = FastAPI(title="Local Gamepad Viewer (Phase 2)")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(lambda m: print(m, end=""), level="INFO")

    # Storage & state bootstrap
    slot_path = slot_file_path()
    config_path = DATA_DIR / "config.json"
    store = FileStore(slot_path=slot_path, config_path=config_path)

    # Initial state (prefer persisted; fallback to defaults)
    persisted = store.read_config()
    init_skin = (persisted["skin"] if persisted else "white")
    # Player: from saved slot (highest), else persisted config, else 1
    slot = store.read_slot()
    init_player = slot["player"] or (persisted["player"] if persisted else 1)
    state = AppState(AppConfig(skin=init_skin, player=init_player))

    # Static mounts
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=False), name="ui")
    if STATIC_SERVER_DIR.exists():
        app.mount("/server/static", StaticFiles(directory=STATIC_SERVER_DIR, html=False), name="server-static")
    if CTRL_DIR.exists():
        app.mount("/controller_css", StaticFiles(directory=CTRL_DIR, html=False), name="controller-css")
    if THEMES_DIR.exists():
        app.mount("/themes", StaticFiles(directory=THEMES_DIR, html=False), name="themes")

    # Core “page” endpoints
    app.include_router(core_router(UI_PAGES))

    # API endpoints
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    app.include_router(config_router(
        state=state,
        storage=store,
        host=host,
        port=port,
        index_css_path=INDEX_CSS_PATH
    ))
    app.include_router(slot_router(state=state, storage=store))
    app.include_router(themes_router())

    # Dynamic vars.css (served under the controller_css path)
    @app.get(VARS_CSS_HTTP, include_in_schema=False)
    async def dynamic_vars_css():
        # We derive the selected skin's folder relative URL: /themes/<skin>
        cfg = state.get()
        skin_folder_rel = f"themes/{cfg.skin}"
        css_bytes = build_vars_css(skin_folder_rel, REQUIRED_FILES)
        return Response(content=css_bytes, media_type="text/css; charset=utf-8")

    return app

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    logger.info(f"Starting dev server on http://{host}:{port}")
    uvicorn.run("app:create_app", host=host, port=port, factory=True, reload=True)
