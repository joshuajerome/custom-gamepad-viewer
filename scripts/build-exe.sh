#!/usr/bin/env zsh
set -euo pipefail

# Run from repo root
cd "$(cd -- "$(dirname -- "$0")"/.. && pwd)"

# --- helpers ---
assert_path() { [ -e "$1" ] || { echo "Required path not found: $1" >&2; exit 1; }; }

# Prefer venv Python if exists, else system
if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi
[[ -n "$PY" ]] || { echo "Python not found"; exit 1; }

# Ensure PyInstaller is available (install into venv if used)
if ! "$PY" -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller not found; installing…"
  "$PY" -m pip install --upgrade pip >/dev/null
  "$PY" -m pip install pyinstaller
fi

# --- validate inputs ---
assert_path "app.py"
assert_path "controller_css"
assert_path "themes"
assert_path "index.html"
assert_path "server/static"

# --- clean old artifacts ---
echo "=== Cleaning old builds ==="
rm -rf build dist || true
rm -f local-gamepad-viewer.spec || true

# On mac/Linux the data-separator is ':'
data_sep=":"

add_data_arg() {
  # prints two args: flag and value
  echo "--add-data"
  echo "$1${data_sep}$2"
}

# --- build options (console only) ---
opts=(
  --onefile
  --noconfirm
  --clean
  --console
  --name local-gamepad-viewer
  $(add_data_arg "controller_css" "controller_css")
  $(add_data_arg "themes" "themes")
  $(add_data_arg "index.html" ".")
  $(add_data_arg "server/static" "server/static")
)

echo "=== Building ==="
echo "Python: $("$PY" -c 'import sys; print(sys.executable)')"
"$PY" -m PyInstaller "${opts[@]}" app.py

echo
echo "=== Done! ==="
echo "Output: dist/local-gamepad-viewer"
echo
echo "Run it with:"
echo "  ./dist/local-gamepad-viewer"
