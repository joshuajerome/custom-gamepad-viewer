# app.py

import os
import sys
from pathlib import Path

def _set_workdir() -> None:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller --onefile: extracted bundle dir
        base = Path(sys._MEIPASS)
    else:
        # Dev/py run or --onedir: folder where app.py lives
        base = Path(__file__).resolve().parent
    os.chdir(base)

_set_workdir()

# Now it is safe to import the app, which expects relative paths to exist.
from server.cli import main  # noqa: E402 (import after chdir on purpose)

if __name__ == "__main__":
    # Optional: quick sanity logs
    from loguru import logger
    logger.info("CWD set to {}", Path.cwd())
    logger.info(
        "Exists css? {}  themes? {}  overlay? {}",
        Path("controller_css").exists(),
        Path("themes").exists(),
        Path("server/static/overlay.html").exists(),
    )
    main()
