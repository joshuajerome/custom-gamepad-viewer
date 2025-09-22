from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger

# --- Paths ---
REPO_ROOT = Path(__file__).resolve().parent
UI_DIR = REPO_ROOT / "ui"
UI_PAGES = UI_DIR / "pages"
STATIC_SERVER_DIR = REPO_ROOT / "server" / "static"
DATA_DIR = REPO_ROOT / "data"

# --- App factory ---
def create_app() -> FastAPI:
    app = FastAPI(title="Local Gamepad Viewer (Phase 0)")

    # Ensure data dir exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Logs
    logger.remove()
    logger.add(lambda m: print(m, end=""), level="INFO")

    # Static mounts (UI + server/static placeholder)
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=False), name="ui")
    if STATIC_SERVER_DIR.exists():
        app.mount("/server/static", StaticFiles(directory=STATIC_SERVER_DIR, html=False), name="server-static")

    # Health
    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    # Root → serve UI page
    @app.get("/")
    async def index() -> Response:  # <-- annotate as Response (or omit annotation)
        index_html = UI_PAGES / "index.html"
        if not index_html.exists():
            return PlainTextResponse("Missing ui/pages/index.html", status_code=500)
        return FileResponse(index_html)

    return app


# --- dev runner ---
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    logger.info(f"Starting dev server on http://{host}:{port}")
    uvicorn.run("app_server:create_app", host=host, port=port, factory=True, reload=True)
