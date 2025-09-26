"""URL service.

Builds the Gamepad Viewer URL using the current player and the local layout.css
endpoint so UI previews are always up to date.
"""

from __future__ import annotations

def build_gpv_url(*, host: str, port: int, player: int, index_css_path: str) -> str:
    css_url = f"http://{host}:{port}/{index_css_path}"
    p = player if 1 <= int(player) <= 4 else 1
    return f"https://gamepadviewer.com/?p={p}&s=5&editcss={css_url}"
