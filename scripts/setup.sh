#!/usr/bin/env bash

# Cross-platform (macOS/Linux) setup script.
# Installs uv if missing, sources uv's env shim, installs uv-managed CPython,
# creates a clean .venv from uv's interpreter, and runs `uv sync`.

set -euo pipefail
cd "$(dirname "$0")/.."

clean=0
build=0
for arg in "$@"; do
  case "$arg" in
    --clean) clean=1 ;;
    --build) build=1 ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

remove_if_exists() {
  local p="$1"
  if [ -e "$p" ]; then
    rm -rf "$p" && echo "Removed $p"
  fi
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  echo "uv not found. Installing uv..." >&2
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Source uv's session shim if present (preferred), otherwise prepend ~/.local/bin
  if [ -f "$HOME/.local/bin/env" ]; then
    # shellcheck disable=SC1090
    . "$HOME/.local/bin/env"
  else
    export PATH="$HOME/.local/bin:$PATH"
  fi

  if ! command -v uv >/dev/null 2>&1; then
    echo "uv installed, but not on PATH. Add '$HOME/.local/bin' to PATH and re-run." >&2
    exit 1
  fi
}

if [ "$clean" -eq 1 ]; then
  echo "Cleaning workspace..."
  remove_if_exists ".venv"
  remove_if_exists "build"
  remove_if_exists "dist"
  find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
  rm -f ./*.spec
  echo "Clean complete."
fi

if [ "$build" -eq 1 ]; then
  ensure_uv
  echo "[1/7] Using uv: $(command -v uv)"

  # Non-interactive: never prompt
  export UV_NO_PROMPT=1

  echo "[2/7] Ensuring uv-managed CPython 3.12 is installed..."
  uv python install 3.12

  # Resolve uv-managed interpreter path (not Anaconda)
  UV_PY="$(uv run --python 3.12 -- python -c 'import sys; print(sys.executable)')"
  echo "Using uv-managed Python: $UV_PY"

  echo "[3/7] Creating uv-managed virtual environment (.venv) with CPython 3.12 (clearing if exists)..."
  uv venv --python "$UV_PY" --clear .venv

  echo "[4/7] Activating virtual environment..."
  # shellcheck disable=SC1091
  source .venv/bin/activate

  echo "[5/7] Syncing project dependencies with uv..."
  uv sync

  echo "[6/7] Verifying interpreter (should be uv-managed 3.12)..."
  python -V
  python -c 'import sys, platform; print(sys.executable); print(platform.python_implementation())'

  echo "[7/7] Which python?"
  command -v python

  echo
  echo "Setup complete! Next steps:"
  echo "  source .venv/bin/activate"
  echo "  python app.py"
fi

if [ "$clean" -eq 0 ] && [ "$build" -eq 0 ]; then
  echo "Usage: ./scripts/setup.sh --build  or  ./scripts/setup.sh --clean"
  exit 1
fi
