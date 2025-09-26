"""Storage protocol and payload shapes.

Defines TypedDicts for JSON payloads and a `Storage` Protocol declaring the
methods required by the server. Enables swapping FileStore with other backends
(e.g., SQLite) without touching the API layer.
"""

from __future__ import annotations
from typing import Protocol, TypedDict

class SlotPayload(TypedDict):
    index: int | None
    player: int | None

class ConfigPayload(TypedDict):
    skin: str
    player: int

class Storage(Protocol):
    def read_slot(self) -> SlotPayload: ...
    def write_slot(self, index: int) -> SlotPayload: ...
    def read_config(self) -> ConfigPayload | None: ...
    def write_config(self, skin: str, player: int) -> ConfigPayload: ...
