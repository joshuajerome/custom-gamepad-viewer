#!/usr/bin/env bash
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
  [ -e "$p" ] && rm -rf "$p" && echo "Removed $p"
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  echo "uv not found. Installing uv..." >&2
  # Official installer; installs to ~/.local/bin by default
  # See: https://astral.sh/uv/docs/install/
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Make uv available immediately in this shell
  export PATH="$HOME/.local/bin:$PATH"
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
  find . -type d -name "__pycache__" -prune -exec rm -rf {} +
  rm -f ./*.spec
  echo "Clean complete."
fi

if [ "$build" -eq 1 ]; then
  ensure_uv
  echo "[1/5] Using uv: $(command -v uv)"
  echo "[2/5] Creating uv-managed virtual environment (.venv) with CPython 3.12..."
  uv venv --python 3.12 .venv

  echo "[3/5] Activating virtual environment..."
  # shellcheck disable=SC1091
  source .venv/bin/activate

  echo "[4/5] Syncing project dependencies with uv..."
  uv sync

  echo "[5/5] Verifying interpreter..."
  python -V
  command -v python

  echo
  echo "Setup complete! Next steps:"
  echo "  source .venv/bin/activate"
  echo "  python app_server.py"
fi

if [ "$clean" -eq 0 ] && [ "$build" -eq 0 ]; then
  echo "Usage: ./scripts/setup.sh --build  or  ./scripts/setup.sh --clean"
  exit 1
fi
#!/usr/bin/env bash
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
  [ -e "$p" ] && rm -rf "$p" && echo "Removed $p"
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  echo "uv not found. Installing uv..." >&2
  # Official installer; installs to ~/.local/bin by default
  # See: https://astral.sh/uv/docs/install/
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Make uv available immediately in this shell
  export PATH="$HOME/.local/bin:$PATH"
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
  find . -type d -name "__pycache__" -prune -exec rm -rf {} +
  rm -f ./*.spec
  echo "Clean complete."
fi

if [ "$build" -eq 1 ]; then
  ensure_uv
  echo "[1/5] Using uv: $(command -v uv)"
  echo "[2/5] Creating uv-managed virtual environment (.venv) with CPython 3.12..."
  uv venv --python 3.12 .venv

  echo "[3/5] Activating virtual environment..."
  # shellcheck disable=SC1091
  source .venv/bin/activate

  echo "[4/5] Syncing project dependencies with uv..."
  uv sync

  echo "[5/5] Verifying interpreter..."
  python -V
  command -v python

  echo
  echo "Setup complete! Next steps:"
  echo "  source .venv/bin/activate"
  echo "  python app_server.py"
fi

if [ "$clean" -eq 0 ] && [ "$build" -eq 0 ]; then
  echo "Usage: ./scripts/setup.sh --build  or  ./scripts/setup.sh --clean"
  exit 1
fi
#!/usr/bin/env bash
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
  [ -e "$p" ] && rm -rf "$p" && echo "Removed $p"
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  echo "uv not found. Installing uv..." >&2
  # Official installer; installs to ~/.local/bin by default
  # See: https://astral.sh/uv/docs/install/
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Make uv available immediately in this shell
  export PATH="$HOME/.local/bin:$PATH"
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
  find . -type d -name "__pycache__" -prune -exec rm -rf {} +
  rm -f ./*.spec
  echo "Clean complete."
fi

if [ "$build" -eq 1 ]; then
  ensure_uv
  echo "[1/5] Using uv: $(command -v uv)"
  echo "[2/5] Creating uv-managed virtual environment (.venv) with CPython 3.12..."
  uv venv --python 3.12 .venv

  echo "[3/5] Activating virtual environment..."
  # shellcheck disable=SC1091
  source .venv/bin/activate

  echo "[4/5] Syncing project dependencies with uv..."
  uv sync

  echo "[5/5] Verifying interpreter..."
  python -V
  command -v python

  echo
  echo "Setup complete! Next steps:"
  echo "  source .venv/bin/activate"
  echo "  python app_server.py"
fi

if [ "$clean" -eq 0 ] && [ "$build" -eq 0 ]; then
  echo "Usage: ./scripts/setup.sh --build  or  ./scripts/setup.sh --clean"
  exit 1
fi
