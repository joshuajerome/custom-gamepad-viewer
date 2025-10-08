"""Connection hub for realtime updates over WebSockets.

Holds a set of active connections and offers `broadcast_json()` to push updates
to all subscribers. Designed to be dependency-free and app-scoped.
"""

from __future__ import annotations
from typing import Set, Any
from loguru import logger
from starlette.websockets import WebSocket, WebSocketDisconnect

class WsHub:
    """Minimal WebSocket connection manager with JSON broadcast."""

    def __init__(self) -> None:
        self._conns: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._conns.add(ws)
        logger.debug("WS connected; total=%d", len(self._conns))

    def _drop(self, ws: WebSocket) -> None:
        if ws in self._conns:
            self._conns.remove(ws)
            logger.debug("WS disconnected; total=%d", len(self._conns))

    async def disconnect(self, ws: WebSocket) -> None:
        self._drop(ws)
        try:
            await ws.close()
        except Exception:
            pass

    async def broadcast_json(self, message: Any) -> None:
        """Send a JSON-serializable object to all active sockets."""
        dead: list[WebSocket] = []
        for ws in self._conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._drop(ws)
