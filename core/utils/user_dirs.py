"""Per-OS user directories.

Computes the app's data directory, user themes directory, and slot file path for
Windows, macOS, and Linux following platform conventions.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

APP_NAME = "Custom Gamepad Viewer"

def data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / APP_NAME
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return base / "local-gamepad-viewer"

def user_themes_dir() -> Path:
    p = data_dir() / "themes"
    p.mkdir(parents=True, exist_ok=True)
    return p

def slot_file_path() -> Path:
    p = data_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p / "slot.json"
