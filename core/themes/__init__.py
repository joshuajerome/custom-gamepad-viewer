"""Theme domain package.

Contains skin discovery (built-in, user, extra paths), asset validation, and
preview URL helpers that are framework-agnostic and reusable by any UI.
"""

from .discovery import discover_builtins, discover_all
from .validate import REQUIRED_FILES, validate_theme_folder
from .preview import build_preview_urls
