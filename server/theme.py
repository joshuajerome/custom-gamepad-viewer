# server/theme.py
from typing import Dict

def build_vars_css(skin_folder: str, var_files: Dict[str, str]) -> bytes:
    """
    Generate:
        :root {
          --base: url("/themes/<skin>/Base.png");
          ...
        }
    """
    lines = [":root {"]
    for var, filename in var_files.items():
        url_path = f"/{skin_folder}/{filename}"
        lines.append(f'  --{var}: url("{url_path}");')
    lines.append("}")
    return ("\n".join(lines)).encode("utf-8")
