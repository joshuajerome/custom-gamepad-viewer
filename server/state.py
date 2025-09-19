# server/state.py
from dataclasses import dataclass
from threading import RLock
from typing import Literal

Skin = Literal["white", "black"]

@dataclass
class AppStateData:
    skin: Skin = "white"
    player: int = 1

class AppState:
    def __init__(self, initial: AppStateData | None = None):
        self._lock = RLock()
        self._data = initial or AppStateData()

    def get(self) -> AppStateData:
        with self._lock:
            return AppStateData(skin=self._data.skin, player=self._data.player)

    def set_skin(self, skin: Skin):
        with self._lock:
            self._data.skin = skin

    def set_player(self, player: int):
        if not (1 <= int(player) <= 4):
            return
        with self._lock:
            self._data.player = int(player)
