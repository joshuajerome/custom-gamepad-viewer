"""Slot API routes.

- GET /api/slot           → returns last saved {index, player}
- POST /api/slot {index}  → saves index atomically, updates player (index+1)

Used by the slot checker page or any UI to bind the active gamepad index.
"""

from __future__ import annotations
from typing import Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from server.state import AppState
from server.storage.base import Storage

def get_router(*, state: AppState, storage: Storage) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/slot")
    async def get_slot():
        return JSONResponse(storage.read_slot())

    @router.post("/slot")
    async def post_slot(body: Dict):
        try:
            index = int(body["index"])
            if index < 0:
                raise ValueError()
        except Exception:
            raise HTTPException(400, 'Expected JSON {"index": <non-negative int>}')

        payload = storage.write_slot(index)
        # update state player
        if payload.get("player"):
            state.set_player(int(payload["player"]))
        return JSONResponse(payload)

    return router
