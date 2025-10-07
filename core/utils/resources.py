"""Resource path resolution.

Provides `repo_root()` that works in both dev and PyInstaller-frozen builds, and
`resolve_resource()` to locate files relative to the application root.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

def _frozen_base() -> Path | None:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        executable_dir = Path(sys.executable).resolve().parent
        if sys.platform == "darwin" and ".app/Contents/MacOS" in str(executable_dir):
            if "Frameworks" in executable_dir.parts:
                idx = executable_dir.parts.index("Frameworks")
                return Path(*executable_dir.parts[:idx])
            return executable_dir.parent
        return executable_dir
    return None

def repo_root() -> Path:
    """
    Best-effort location of the application root:
      - if frozen: bundle base
      - else: cwd file parent (two levels up from this file)
    """
    base = _frozen_base()
    if base:
        return base
    return Path(__file__).resolve().parents[2]

def resolve_resource(*parts: str) -> Path:
    """
    Resolve a resource path both in dev and when frozen.
    """
    return repo_root().joinpath(*parts)
