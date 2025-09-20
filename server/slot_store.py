# server/slot_store.py
from pathlib import Path
from loguru import logger
import json
import os
import threading
import time
from typing import Optional, Tuple

class SlotStore:
    """
    Thread-safe read/write for slot.json (Windows-friendly with lock + retry).
    """
    def __init__(self, path: str):
        self.path = Path(path)
        self._lock = threading.Lock()
        # Ensure directory exists for both read/write scenarios
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read_player(self) -> Optional[int]:
        with self._lock:
            if not self.path.exists():
                return None
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                player = int(data.get("player", 0))
                return player if 1 <= player <= 4 else None
            except Exception as e:
                logger.warning("Failed to read {}: {}", self.path, e)
                return None

    def read_raw(self) -> bytes:
        with self._lock:
            if self.path.exists():
                return self.path.read_bytes()
            return b'{"index": null, "player": null}'

    def save_index(self, index: int) -> Tuple[int, bytes]:
        if index < 0:
            raise ValueError("index must be >= 0")
        player = index + 1
        payload = {"index": index, "player": player}
        payload_bytes = json.dumps(payload, indent=2).encode("utf-8")

        # Ensure parent dir exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        tmp = self.path.with_suffix(self.path.suffix + ".tmp")

        with self._lock:
            # Write temp
            tmp.write_bytes(payload_bytes)

            # Retry replace (Windows friendliness)
            for attempt in range(1, 11):
                try:
                    os.replace(tmp, self.path)
                    break
                except PermissionError as e:
                    if attempt == 10:
                        raise
                    time.sleep(0.05)
        logger.info("Saved slot: index={} -> player p={}", index, player)
        return player, payload_bytes
