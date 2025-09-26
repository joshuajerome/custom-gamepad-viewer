"""Theme validation.

Defines the required PNG filenames and validates a theme folder for presence of
those files (dimension/rules can be added later). Returns a simple result model.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

REQUIRED_FILES: Dict[str, str] = {
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

@dataclass(frozen=True)
class ThemeValidation:
    ok: bool
    missing: List[str]

def validate_theme_folder(folder: Path) -> ThemeValidation:
    """
    Check presence of required asset PNGs. Dimension checks will be added later.
    """
    missing = [fname for fname in REQUIRED_FILES.values() if not (folder / fname).exists()]
    return ThemeValidation(ok=len(missing) == 0, missing=missing)
