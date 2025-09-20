# server/config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

@dataclass(frozen=True)
class Config:
    host: str = "127.0.0.1"
    port: int = 8000

    # Relative to repo root (served as static)
    index_css_path: str = "controller_css/layout.css"   # GPV should load this
    vars_css_path:  str = "controller_css/vars.css"     # generated on the fly
    slot_json_path: str = "tmp/slot.json"        # persisted slot info

    # Available skins (relative to repo root)
    skin_folders: Dict[str, str] = None

    # Image variable → filename
    var_files: Dict[str, str] = None

    def __post_init__(self):
        if self.skin_folders is None:
            object.__setattr__(self, "skin_folders", {
                "black": "themes/black",
                "white": "themes/white",
            })
        if self.var_files is None:
            object.__setattr__(self, "var_files", {
                "base":         "Base.png",
                "disconnected": "Disconnected.png",
                "trigger":      "Trigger.png",
                "bumper":       "Bumper.png",
                "touchpad":     "Touchpad.png",
                "meta":         "Meta.png",
                "start":        "Start.png",
                "face":         "Face.png",
                "stick":        "Stick.png",
                "dpad":         "Dpad.png",
            })

    # Convenience
    def index_css_exists(self) -> bool:
        return Path(self.index_css_path).exists()

    def skin_paths_exist(self) -> bool:
        return all(Path(p).exists() for p in self.skin_folders.values())
