from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Skin = str  # e.g., "white", "black"

@dataclass(frozen=True)
class PreviewURLs:
    gpv_url: str
    css_url: str
    skin: Skin
    player: int

def build_preview_urls(
    *,
    host: str,
    port: int,
    player: int,
    index_css_path: str = "controller_css/layout.css",
) -> PreviewURLs:
    """
    Build URLs consumed by Gamepad Viewer and the local CSS endpoint.
    Note: vars.css will be served by the backend route; not needed here.

    Example GPV URL:
      https://gamepadviewer.com/?p=1&s=5&editcss=http://127.0.0.1:8000/controller_css/layout.css
    """
    player = int(player)
    if not (1 <= player <= 4):
        player = 1

    css_url = f"http://{host}:{port}/{index_css_path}"
    gpv_url = f"https://gamepadviewer.com/?p={player}&s=5&editcss={css_url}"
    return PreviewURLs(gpv_url=gpv_url, css_url=css_url, skin="", player=player)
