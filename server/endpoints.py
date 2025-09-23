from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse

def get_router(ui_pages_dir: Path) -> APIRouter:
    router = APIRouter()

    @router.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    @router.get("/", include_in_schema=False)
    async def index():
        index_html = ui_pages_dir / "index.html"
        if not index_html.exists():
            return PlainTextResponse("Missing ui/pages/index.html", status_code=500)
        return FileResponse(index_html)

    @router.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        svg = ui_pages_dir.parent / "assets" / "favicon.svg"
        if svg.exists():
            return FileResponse(svg, media_type="image/svg+xml")
        return PlainTextResponse("", status_code=404)

    return router