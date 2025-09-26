"""Theme CSS builder service.

Generates the :root { --var: url("/themes/<skin>/File.png"); ... } block used by
layout.css so that the active skin swaps image assets without editing CSS files.
"""

from __future__ import annotations
from typing import Dict
from pathlib import Path

def build_vars_css(skin_folder_rel: str, required_files: Dict[str, str]) -> bytes:
    """
    Generate:
      :root {
        --base: url("/themes/<skin>/Base.png");
        ...
      }
    """
    folder_url = "/" + str(Path(skin_folder_rel).as_posix()).lstrip("/")
    lines = [":root {"]
    for var, filename in required_files.items():
        url_path = f'{folder_url}/{filename}'
        lines.append(f'  --{var}: url("{url_path}");')
    lines.append("}")
    return ("\n".join(lines)).encode("utf-8")
