# build-exe.ps1
# -------------------------------------------
# Build an EXE with PyInstaller.
# Output: dist/local-gamepad-viewer.exe
# -------------------------------------------

$ErrorActionPreference = "Stop"

function Assert-Path($p) {
  if (-not (Test-Path $p)) {
    Write-Error "Required path not found: $p"
  }
}

# Validate required paths
Assert-Path "app.py"
Assert-Path "controller_css"
Assert-Path "themes"
Assert-Path "index.html"
Assert-Path "server\static"

Write-Host "=== Cleaning old builds ==="
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item local-gamepad-viewer.spec -ErrorAction SilentlyContinue

$opts = @(
  "--onefile",
  "--noconfirm",
  "--clean",
  "--console",
  "--name", "local-gamepad-viewer",
  "--add-data", "controller_css;controller_css",
  "--add-data", "themes;themes",
  "--add-data", "index.html;.",
  "--add-data", "server/static;server/static"
)

Write-Host "=== Building (onefile) ==="
py -m PyInstaller @opts app.py

Write-Host ""
Write-Host "=== Done! ==="
Write-Host "Output:"
Write-Host "  dist\local-gamepad-viewer.exe"
Write-Host ""

