from __future__ import annotations
import os
import sys
from pathlib import Path

def _frozen_base() -> Path | None:
    # PyInstaller onefile/onedir extraction dir
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
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
