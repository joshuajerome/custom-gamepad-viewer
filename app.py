# app.py
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from server.endpoints import get_router

REPO_ROOT = Path(__file__).resolve().parent
UI_DIR = REPO_ROOT / "ui"
UI_PAGES = UI_DIR / "pages"
STATIC_SERVER_DIR = REPO_ROOT / "server" / "static"
DATA_DIR = REPO_ROOT / "data"

def create_app() -> FastAPI:
    app = FastAPI(title="Local Gamepad Viewer (Phase 0/1)")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(lambda m: print(m, end=""), level="INFO")

    # Static mounts
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=False), name="ui")
    if STATIC_SERVER_DIR.exists():
        app.mount("/server/static", StaticFiles(directory=STATIC_SERVER_DIR, html=False), name="server-static")

    app.include_router(get_router(UI_PAGES))

    return app


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    logger.info(f"Starting dev server on http://{host}:{port}")
    uvicorn.run("app:create_app", host=host, port=port, factory=True, reload=True)
