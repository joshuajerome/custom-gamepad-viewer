# server/theme.py
from typing import Dict
from pathlib import Path

def build_vars_css(skin_folder: str, var_files: Dict[str, str]) -> bytes:
    """
    Generate CSS like:
        :root {
          --base: url("/themes/white/Base.png");
          ...
        }
    """
    folder_url = "/" + str(Path(skin_folder).as_posix()).lstrip("/")
    lines = [":root {"]
    for var, filename in var_files.items():
        url_path = f"{folder_url}/{filename}"
        lines.append(f'  --{var}: url("{url_path}");')
    lines.append("}")
    return ("\n".join(lines)).encode("utf-8")
