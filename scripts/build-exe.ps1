# Build Windows executable into dist/ using PyInstaller.
# Aligns with CI workflow flags and local repo layout.

param(
  [switch]$Clean,
  [switch]$OneFile,    # optional: force onefile
  [switch]$Onedir,     # optional: force onedir
  [switch]$Console,    # optional: keep console window (default is windowed)
  [string]$Name = "CustomGamepadViewer"
)

$ErrorActionPreference = "Stop"

# Move to repo root
Set-Location -LiteralPath (Resolve-Path "$PSScriptRoot\..")

function Remove-IfExists([string]$Path) {
  if (Test-Path -LiteralPath $Path) {
    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Removed $Path"
  }
}

if ($Clean) {
  Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
  Remove-IfExists "build"
  Remove-IfExists "dist"
  Get-ChildItem -LiteralPath . -Filter *.spec -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
  }
}

# Ensure a Python env is available (prefer project .venv)
$venvPython = Join-Path ".\.venv\Scripts" "python.exe"
if (Test-Path -LiteralPath $venvPython) {
  $python = $venvPython
  . .\.venv\Scripts\Activate.ps1
} else {
  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd) {
    $python = $pythonCmd.Path
  } else {
    Write-Host "No Python or .venv found; running setup to create .venv..." -ForegroundColor Yellow
    . .\scripts\setup.ps1 -build
    . .\.venv\Scripts\Activate.ps1
    $python = $venvPython
  }
}

if (-not $python -or -not (Test-Path -LiteralPath $python)) {
  throw "Python interpreter not found. Please run scripts/setup.ps1 -build first."
}

# Ensure pip present and PyInstaller installed
& $python -m ensurepip --upgrade | Out-Null

$pyi = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyi) {
  Write-Host "Installing PyInstaller into the active environment..." -ForegroundColor Cyan
  & $python -m pip install "pyinstaller>=6.9,<7"
}

# Compose PyInstaller arguments
$argsList = @(
  "--noconfirm",
  "--clean"
)

# Avoid UPX by default (can trigger AV heuristics)
$argsList += "--noupx"

# Choose onefile by default unless explicitly overridden
$useOneFile = $true
if ($Onedir) { $useOneFile = $false }
if ($OneFile) { $useOneFile = $true }
if ($useOneFile) { $argsList += "--onefile" } else { $argsList += "--onedir" }

$argsList += @(
  "--name", $Name
)

# Hide console window by default (GUI subsystem). Use -Console to keep it.
if (-not $Console) { $argsList += "--windowed" }

# Icon (optional)
$ico = "packaging\windows\CustomGamepadViewer.ico"
if (Test-Path -LiteralPath $ico) {
  $argsList += @("--icon", $ico)
}

# Static/data folders
$argsList += @(
  "--add-data", "ui;ui",
  "--add-data", "controller_css;controller_css",
  "--add-data", "themes;themes"
)

if (Test-Path -LiteralPath "server\static") {
  $argsList += @("--add-data", "server/static;server/static")
}

# NiceGUI data files only (keeps build smaller than --collect-all)
$argsList += @("--collect-data", "nicegui")

# Also drop the ICO into exe dir at runtime for taskbar/Tk usage
if (Test-Path -LiteralPath $ico) {
  $argsList += @("--add-data", "packaging\\windows\\CustomGamepadViewer.ico;.")
}

$argsList += "app.py"

Write-Host "Running: pyinstaller $($argsList -join ' ')" -ForegroundColor Green
pyinstaller @argsList

Write-Host "\nBuild complete. See: dist\$Name$([bool]$useOneFile -replace '^True$','.exe' -replace '^False$','')" -ForegroundColor Green
if (-not $useOneFile) {
  Write-Host "Tip: pass -OneFile to create a single EXE (larger startup stub)." -ForegroundColor DarkGray
}
