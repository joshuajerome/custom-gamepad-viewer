"""Storage protocol and payload shapes.

Defines TypedDicts for JSON payloads and a `Storage` Protocol declaring the
methods required by the server. Enables swapping FileStore with other backends
(e.g., SQLite) without touching the API layer.
"""

from __future__ import annotations
from typing import NotRequired, Protocol, TypedDict

class SlotPayload(TypedDict):
    index: int | None
    player: int | None

class LauncherSettingsPayload(TypedDict, total=False):
    host: str
    port: int
    hotkey: str

class ConfigPayload(TypedDict, total=False):
    skin: str
    player: int
    launcher: NotRequired[LauncherSettingsPayload]

class Storage(Protocol):
    def read_slot(self) -> SlotPayload: ...
    def write_slot(self, index: int) -> SlotPayload: ...
    def read_config(self) -> ConfigPayload | None: ...
    def write_config(self, skin: str, player: int) -> ConfigPayload: ...
    def write_launcher_settings(self, launcher: LauncherSettingsPayload) -> ConfigPayload: ...
