from pathlib import Path
from core.themes.discovery import discover_builtins

def test_discover_builtins_exists():
    mapping = discover_builtins()
    assert isinstance(mapping, dict)
    # if repo has built-ins, they should appear here
