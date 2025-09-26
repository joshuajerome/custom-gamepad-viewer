"""Core utility package.

Holds environment-agnostic helpers for resolving resource paths (dev vs frozen),
per-OS user data directories, and user themes/slot file locations.
"""

from .resources import repo_root, resolve_resource
from .user_dirs import data_dir, user_themes_dir, slot_file_path
