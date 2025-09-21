#!/usr/bin/env zsh
set -euo pipefail

cd "$(cd -- "$(dirname -- "$0")"/.. && pwd)"

clean=false
build=false
for arg in "$@"; do
  case "$arg" in
    --clean) clean=true ;;
    --build) build=true ;;
  esac
done

remove_if_exists() {
  local p="$1"
  if [ -e "$p" ]; then
    rm -rf "$p"
    echo "  Removed $p"
  fi
}

remove_glob() {
  local pattern="$1"
  # quietly handle no matches
  for f in ${(~)pattern}; do
    [ -e "$f" ] && rm -rf "$f" && echo "  Removed $f"
  done
}

if $clean; then
  echo "Cleaning workspace..."

  # Deactivate any active venv (best effort)
  if [ -n "${VIRTUAL_ENV:-}" ] && [ -d "$VIRTUAL_ENV" ]; then
    echo "  Deactivating active virtual environment..."
    deactivate 2>/dev/null || true
    unset VIRTUAL_ENV
  fi

  # Project venv
  remove_if_exists ".venv"

  # PyInstaller artifacts
  remove_if_exists "build"
  remove_if_exists "dist"
  remove_glob "local-gamepad-viewer.spec"

  # Python caches
  find . -type d -name "__pycache__" -print0 | xargs -0 rm -rf || true
  find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete || true

  echo "Clean complete."
fi

if $build; then
  echo "[1/4] Creating Python virtual environment (.venv)..."
  command -v python3 >/dev/null 2>&1 || { echo "python3 not found. On mac: brew install python"; exit 1; }
  python3 -m venv .venv

  echo "[2/4] Activating virtual environment..."
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "  Using: $(python -c 'import sys; print(sys.executable)')"

  echo "[3/4] Installing uv..."
  python -m pip install --upgrade pip
  python -m pip install uv

  echo "[4/4] Initializing uv project..."
  uv sync

  echo "Environment setup complete!"
fi

if ! $clean && ! $build; then
  echo "Usage: ./scripts/setup.sh --clean [--build]  |  ./scripts/setup.sh --build"
  echo "Note: To keep the venv active in your current shell, run: source scripts/setup.sh --build"
  exit 1
fi
