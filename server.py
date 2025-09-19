"""
Gamepad Viewer Dev Server
-------------------------

Serves local CSS/PNG assets for Gamepad Viewer with a convenient skin toggle.
Also exposes any static files in the current directory (so your check_slot.html
is served directly).

Usage examples:
    python server.py
    python server.py --skin white --p 1
    python server.py --skin black --p 2

By default the server binds to 127.0.0.1:8000.
"""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
from loguru import logger
import argparse
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = "127.0.0.1"
PORT = 8000

# Path to the CSS that Gamepad Viewer should load (relative to server root)
INDEX_CSS_PATH = "ps5_gpv/white/index.css"

# Subfolders that hold your PNG sets (relative to INDEX_CSS_PATH’s directory)
SKIN_FOLDERS = {
    "black": "./black",
    "white": "./white",
}

# Variables exposed by /theme.css -> each maps to a PNG filename
VAR_NAMES = {
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

# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class DevHandler(SimpleHTTPRequestHandler):
    """
    Request handler that disables caching for quick iteration and generates
    /theme.css based on --skin. All other files (including check_slot.html)
    are served as normal static files.
    """
    skin_choice = "white"
    index_css_path = INDEX_CSS_PATH

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/theme.css":
            self._serve_theme_css()
            return
        # All other files (including check_slot.html) handled normally
        return super().do_GET()

    def _serve_theme_css(self):
        folder = SKIN_FOLDERS[self.skin_choice]
        base_dir = "/" + "/".join(self.index_css_path.split("/")[:-1])

        lines = [":root {"]
        for var, filename in VAR_NAMES.items():
            url_path = f'{base_dir}/{folder.strip("./")}/{filename}'
            lines.append(f'  --{var}: url("{url_path}");')
        lines.append("}")
        css = ("\n".join(lines)).encode("utf-8")

        logger.debug("Serving /theme.css (skin='{}')", self.skin_choice)
        self.send_response(200)
        self.send_header("Content-Type", "text/css; charset=utf-8")
        self.send_header("Content-Length", str(len(css)))
        self.end_headers()
        self.wfile.write(css)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_urls(host: str, port: int, index_css_path: str, slot: int) -> tuple[str, str]:
    css_url = f"http://{host}:{port}/{index_css_path}"
    gpv_url = f"https://gamepadviewer.com/?p={slot}&s=5&editcss={css_url}"
    return css_url, gpv_url

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Serve Gamepad Viewer assets with skin toggle.")
    parser.add_argument("--host", default=HOST, help=f"bind address (default: {HOST})")
    parser.add_argument("--port", type=int, default=PORT, help=f"port (default: {PORT})")
    parser.add_argument("--skin", choices=SKIN_FOLDERS.keys(), default="white",
                        help="image set to expose via /theme.css (white|black)")
    parser.add_argument("--p", type=int, choices=range(1, 5), default=2,
                        help="Gamepad Viewer player slot (1-4)")
    parser.add_argument("--index", default=INDEX_CSS_PATH,
                        help=f"path to main CSS relative to server root (default: {INDEX_CSS_PATH})")
    parser.add_argument("--log-level", default="INFO", help="loguru level (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level=args.log_level.upper(),
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

    # Warn if index.css not found
    if not Path(args.index).exists():
        logger.warning("Index CSS not found at {}", args.index)

    DevHandler.skin_choice = args.skin
    DevHandler.index_css_path = args.index

    ThreadingHTTPServer.allow_reuse_address = True
    server_address = (args.host, args.port)

    with ThreadingHTTPServer(server_address, DevHandler) as httpd:
        sa_host, sa_port = httpd.socket.getsockname()
        css_url, gpv_url = build_urls(sa_host, sa_port, args.index, args.p)

        logger.info("HTTP server started on http://{}:{}", sa_host, sa_port)
        logger.info("Skin set to: {}", args.skin)
        logger.info("Serving index.css: {}", css_url)
        logger.info("Gamepad Viewer link: {}", gpv_url)
        logger.info("Slot checker:       http://{}:{}/check_slot.html", sa_host, sa_port)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt; shutting down…")
        finally:
            httpd.server_close()

if __name__ == "__main__":
    try:
        main()
    except OSError as e:
        logger.error("Failed to bind {}:{} -> {}", HOST, PORT, e)
        sys.exit(1)
