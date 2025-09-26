"""Config API routes.

- GET /api/config  → current skin/player, available skins, preview URLs
- POST /api/config → update & persist skin/player
- GET /api/vars.css (via app) → dynamic CSS variables for selected skin

Bridges server state/storage with core theme discovery/validation utilities.
"""

from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.themes.discovery import discover_all
from core.themes.validate import REQUIRED_FILES, validate_theme_folder
from server.state import AppState
from server.storage.base import Storage
from server.services.url_service import build_gpv_url
from server.services.theme_service import build_vars_css

def get_router(
    *,
    state: AppState,
    storage: Storage,
    host: str,
    port: int,
    index_css_path: str,
    themes_root_rel: str = "themes",  # mount root (served statically)
) -> APIRouter:
    router = APIRouter(prefix="/api")

    def _available_skins() -> Dict[str, str]:
        # returns {skin_name: "themes/<skin_name>"}
        mapping: Dict[str, str] = {}
        for name, path, source in discover_all():
            if str(path).endswith(name):  # built-in absolute; convert to relative served path
                mapping[name] = f"{themes_root_rel}/{name}"
            else:
                mapping[name] = f"{themes_root_rel}/{name}"  # same format for simplicity
        return mapping

    @router.get("/config")
    async def get_config():
        cfg = state.get()
        skins = _available_skins()
        if cfg.skin not in skins and skins:
            # choose first available if current missing
            cfg.skin = sorted(skins.keys())[0]  # type: ignore[attr-defined]
            state.set_skin(cfg.skin)
        payload = {
            "skin": cfg.skin,
            "player": cfg.player,
            "available_skins": sorted(skins.keys()),
            "gpv_url": build_gpv_url(host=host, port=port, player=cfg.player, index_css_path=index_css_path),
            "css_url": f"http://{host}:{port}/{index_css_path}",
        }
        return JSONResponse(payload)

    @router.post("/config")
    async def post_config(body: Dict):
        skins = _available_skins()
        if "skin" in body:
            skin = str(body["skin"])
            if skin not in skins:
                raise HTTPException(400, f"Unknown skin '{skin}'")
            state.set_skin(skin)

        if "player" in body:
            try:
                p = int(body["player"])
            except Exception:
                p = 1
            state.set_player(p)

        cfg = state.get()
        # persist
        storage.write_config(cfg.skin, cfg.player)

        payload = {
            "ok": True,
            "skin": cfg.skin,
            "player": cfg.player,
            "gpv_url": build_gpv_url(host=host, port=port, player=cfg.player, index_css_path=index_css_path),
            "css_url": f"http://{host}:{port}/{index_css_path}",
        }
        return JSONResponse(payload)

    # Dynamic vars.css
    @router.get("/vars.css", include_in_schema=False)
    async def vars_css():
        cfg = state.get()
        skins = _available_skins()
        if not skins:
            raise HTTPException(500, "No themes found in /themes")
        skin = cfg.skin if cfg.skin in skins else sorted(skins.keys())[0]
        css_bytes = build_vars_css(skins[skin], REQUIRED_FILES)
        return JSONResponse(content=css_bytes.decode("utf-8"), media_type="text/css; charset=utf-8")

    return router
