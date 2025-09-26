"""Core package export surface.

Re-exports discovery/validation/preview utilities so server/UI layers can import
stable functions from `core` without knowing submodule paths.
"""

from .themes.discovery import discover_builtins, discover_all
from .themes.validate import REQUIRED_FILES, validate_theme_folder
from .themes.preview import build_preview_urls
