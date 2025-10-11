"""JSON file-based storage.

Atomically persists `slot.json` and `config.json` under the user data directory.
Implements the `Storage` protocol for easy substitution in tests or future backends.
"""

from __future__ import annotations
from pathlib import Path
from threading import RLock
import json
import os
import time
from typing import Optional

from server.storage.base import Storage, SlotPayload, ConfigPayload, LauncherSettingsPayload

class FileStore(Storage):
    def __init__(self, slot_path: Path, config_path: Path):
        self.slot_path = slot_path
        self.config_path = config_path
        self.slot_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def _atomic_write(self, path: Path, data: bytes) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        # Windows-friendly retry
        for _ in range(10):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                time.sleep(0.05)
        os.replace(tmp, path)

    # ---- Slot
    def read_slot(self) -> SlotPayload:
        with self._lock:
            if not self.slot_path.exists():
                return {"index": None, "player": None}
            try:
                return json.loads(self.slot_path.read_text(encoding="utf-8"))
            except Exception:
                return {"index": None, "player": None}

    def write_slot(self, index: int) -> SlotPayload:
        player = int(index) + 1
        payload: SlotPayload = {"index": int(index), "player": player}
        data = json.dumps(payload, indent=2).encode("utf-8")
        with self._lock:
            self._atomic_write(self.slot_path, data)
        return payload

    # ---- Config (skin/player)
    def read_config(self) -> Optional[ConfigPayload]:
        with self._lock:
            if not self.config_path.exists():
                return None
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                return None

    def write_config(self, skin: str, player: int) -> ConfigPayload:
        payload: ConfigPayload = {"skin": skin, "player": int(player)}
        existing = self.read_config() or {}
        if launcher := existing.get("launcher"):
            payload["launcher"] = launcher  # type: ignore[index]
        data = json.dumps(payload, indent=2).encode("utf-8")
        with self._lock:
            self._atomic_write(self.config_path, data)
        return payload

    def write_launcher_settings(self, launcher: LauncherSettingsPayload) -> ConfigPayload:
        with self._lock:
            payload: ConfigPayload = self.read_config() or {"skin": "white", "player": 1}
            existing = payload.get("launcher", {}) or {}
            payload["launcher"] = {
                "host": launcher.get("host", existing.get("host", "127.0.0.1")),
                "port": int(launcher.get("port", existing.get("port", 8000))),
                "hotkey": launcher.get("hotkey", existing.get("hotkey", "F2")),
            }
            data = json.dumps(payload, indent=2).encode("utf-8")
            self._atomic_write(self.config_path, data)
            return payload
