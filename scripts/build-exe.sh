#!/usr/bin/env bash

# Build macOS .app bundle into dist/ using PyInstaller.
# Mirrors the CI workflow logic for local Intel/Apple Silicon builds.

set -euo pipefail
cd "$(dirname "$0")/.."

clean=0
zip_output=0
name="CustomGamepadViewer"
spec_path=""

usage() {
  cat <<'EOF'
Usage: ./scripts/build-exe.sh [options]

Options:
  --clean            Remove build artifacts (build/, dist/, *.spec) before building.
  --zip              Zip the generated .app bundle using ditto.
  --name NAME        Override the resulting application name (default: CustomGamepadViewer).
  --spec PATH        Use a specific PyInstaller spec file.
  -h, --help         Show this help text.
EOF
}

while (($#)); do
  case "$1" in
    --clean) clean=1 ;;
    --zip) zip_output=1 ;;
    --name)
      shift || { echo "Missing value for --name" >&2; exit 1; }
      name="$1"
      ;;
    --spec)
      shift || { echo "Missing value for --spec" >&2; exit 1; }
      spec_path="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift || true
done

remove_if_exists() {
  local path="$1"
  if [[ -e "$path" ]]; then
    rm -rf "$path"
    echo "Removed $path"
  fi
}

if [[ "$clean" -eq 1 ]]; then
  echo "Cleaning build artifacts..."
  remove_if_exists "build"
  remove_if_exists "dist"
  find . -maxdepth 1 -name '*.spec' -type f -exec rm -f {} +
fi

# Resolve (and activate) the project virtualenv, falling back to setup.sh --build.
if [[ -x ".venv/bin/python" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
else
  echo "No project .venv detected; running setup to create one..."
  ./scripts/setup.sh --build
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

python -m ensurepip --upgrade >/dev/null

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "Installing PyInstaller (pinned to >=6.9,<7)..." >&2
  python -m pip install "pyinstaller>=6.9,<7"
fi

if [[ -z "$spec_path" && -f "packaging/gamepad.spec" ]]; then
  spec_path="packaging/gamepad.spec"
fi

if [[ -n "$spec_path" ]]; then
  echo "Building via spec file: $spec_path"
  pyinstaller "$spec_path"
else
  args=(
    "--noconfirm"
    "--clean"
    "--windowed"
    "--name" "$name"
    "--add-data" "ui:ui"
    "--add-data" "controller_css:controller_css"
    "--add-data" "themes:themes"
    "--collect-data" "nicegui"
  )

  if [[ -d "server/static" ]]; then
    args+=( "--add-data" "server/static:server/static" )
  fi

  if [[ -f "packaging/macos/CustomGamepadViewer.icns" ]]; then
    args+=( "--icon" "packaging/macos/CustomGamepadViewer.icns" )
  fi

  args+=( "app.py" )

  echo "Running: pyinstaller ${args[*]}"
  pyinstaller "${args[@]}"
fi

bundle_path="dist/${name}.app"

if [[ ! -d "$bundle_path" ]]; then
  echo "Expected bundle not found at $bundle_path" >&2
  exit 1
fi

echo "Build complete. Bundle located at: $bundle_path"

if [[ "$zip_output" -eq 1 ]]; then
  zip_name="${name}-$(uname -m).zip"
  echo "Zipping bundle to dist/$zip_name..."
  (
    cd dist
    ditto -c -k --sequesterRsrc --keepParent "${name}.app" "$zip_name"
  )
  echo "Archive ready: dist/$zip_name"
fi
