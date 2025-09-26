"""Theme discovery utilities.

Finds available skins across sources in precedence order:
  1) extra directories (CLI/UI-added)
  2) per-user themes directory
  3) built-in themes bundled with the app

Returns stable (name, path, source) tuples for consumers.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from core.utils.resources import repo_root
from core.utils.user_dirs import user_themes_dir

# Built-in themes location (inside the repo / bundle)
BUILTINS_DIR = repo_root() / "themes"

def _list_theme_dirs(base: Path) -> List[Path]:
    if not base.exists():
        return []
    return [p for p in base.iterdir() if p.is_dir()]

def discover_builtins() -> Dict[str, Path]:
    """
    Returns {theme_name: absolute_path} for built-in themes bundled with the app.
    """
    mapping: Dict[str, Path] = {}
    for p in _list_theme_dirs(BUILTINS_DIR):
        mapping[p.name] = p
    return mapping

def discover_all(extra_dirs: Iterable[Path] | None = None) -> List[Tuple[str, Path, str]]:
    """
    Discover themes across:
      1) extra_dirs (highest precedence)
      2) user themes dir
      3) built-ins

    Returns a list of (name, path, source) with stable precedence order.
    """
    results: List[Tuple[str, Path, str]] = []

    seen: set[str] = set()
    def add_from(base: Path, source: str):
        nonlocal seen, results
        for p in _list_theme_dirs(base):
            if p.name in seen:
                continue
            results.append((p.name, p, source))
            seen.add(p.name)

    # 1) extra
    if extra_dirs:
        for d in extra_dirs:
            add_from(d, "extra")

    # 2) user dir
    add_from(user_themes_dir(), "user")

    # 3) built-ins
    add_from(BUILTINS_DIR, "builtin")

    return results
