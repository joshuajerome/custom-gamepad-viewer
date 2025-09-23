from pathlib import Path
from core.themes.validate import validate_theme_folder

def test_validate_theme_folder_missing(tmp_path: Path):
    res = validate_theme_folder(tmp_path)
    assert not res.ok
    assert len(res.missing) > 0
