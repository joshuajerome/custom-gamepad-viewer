"""In-memory application state.

Holds the current configuration (skin, player) behind a small lock-protected API.
Routes update this state and persist it via the Storage abstraction.
"""

from __future__ import annotations
from dataclasses import dataclass
from threading import RLock

@dataclass
class AppConfig:
    skin: str = "white"
    player: int = 1  # default player slot number

class AppState:
    def __init__(self, initial: AppConfig | None = None):
        self._lock = RLock()
        self._cfg = initial or AppConfig()

    def get(self) -> AppConfig:
        with self._lock:
            return AppConfig(skin=self._cfg.skin, player=self._cfg.player)

    def set_skin(self, skin: str) -> None:
        with self._lock:
            self._cfg.skin = skin

    def set_player(self, player: int) -> None:
        if not (1 <= int(player) <= 4):
            return
        with self._lock:
            self._cfg.player = int(player)
