# server/config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = REPO_ROOT / "themes"

REQUIRED_FILES = {
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
}

def _discover_skins() -> Dict[str, str]:
    """Return {skin_name: 'themes/<skin_name>'} for each subfolder with at least 1 file."""
    mapping: Dict[str, str] = {}
    if THEMES_DIR.exists():
        for p in THEMES_DIR.iterdir():
            if p.is_dir():
                mapping[p.name] = str(Path("themes") / p.name)
    return mapping

def _missing_files(theme_folder: Path) -> List[str]:
    return [fname for fname in REQUIRED_FILES.values() if not (theme_folder / fname).exists()]

@dataclass(frozen=True)
class Config:
    host: str = "127.0.0.1"
    port: int = 8000

    index_css_path: str = "controller_css/layout.css"
    vars_css_path:  str = "controller_css/vars.css"
    slot_json_path: str = "tmp/slot.json"

    skin_folders: Dict[str, str] = None
    var_files: Dict[str, str] = None

    def __post_init__(self):
        if self.skin_folders is None:
            object.__setattr__(self, "skin_folders", _discover_skins())
        if self.var_files is None:
            object.__setattr__(self, "var_files", REQUIRED_FILES)

    def index_css_exists(self) -> bool:
        return Path(self.index_css_path).exists()

    def available_skins(self) -> List[str]:
        return sorted(self.skin_folders.keys())

    def validate_skin(self, name: str) -> List[str]:
        folder = self.skin_folders.get(name)
        if not folder:
            return ["<theme folder not found>"]
        return _missing_files(REPO_ROOT / folder)
