"""WebSocket endpoint for realtime notifications.

Route:
  - GET /ws (WebSocket): clients subscribe and receive JSON events:
      {"type": "config", "payload": {...}}
      {"type": "slot",   "payload": {...}}

Server POST handlers (config/slot) should call hub.broadcast_json(...)
to push updates to all connected clients.
"""

from __future__ import annotations
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server.realtime.hub import WsHub

def get_router(*, hub: WsHub) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await hub.connect(ws)
        try:
            # Passive channel for now; ignore client messages.
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            await hub.disconnect(ws)
        except Exception:
            await hub.disconnect(ws)

    return router
