"""Themes API route.

- GET /api/themes → enumerates discovered themes with validation status
Allows UIs to show a gallery and surface missing assets for each theme.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.themes.discovery import discover_all
from core.themes.validate import REQUIRED_FILES, validate_theme_folder

def get_router() -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/themes")
    async def get_themes():
        items: List[Dict] = []
        for name, path, source in discover_all():
            v = validate_theme_folder(path)
            items.append({
                "name": name,
                "path": f"themes/{name}",
                "source": source,
                "ok": v.ok,
                "missing": v.missing,
            })
        return JSONResponse({"themes": items})

    return router
