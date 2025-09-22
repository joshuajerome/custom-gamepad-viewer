param(
  [switch]$clean,
  [switch]$build
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Resolve-Path "$PSScriptRoot\..")

function Remove-IfExists([string]$Path) {
  if (Test-Path -LiteralPath $Path) {
    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Removed $Path"
  }
}

function Ensure-Uv {
  $uv = Get-Command uv -ErrorAction SilentlyContinue
  if ($uv) { return $uv.Path }

  Write-Host "uv not found. Installing uv..." -ForegroundColor Yellow
  # Official installer (no admin). Installs into $HOME\.local\bin by default.
  # See: https://astral.sh/uv/docs/install/
  Invoke-Expression (& { (Invoke-WebRequest -UseBasicParsing https://astral.sh/uv/install.ps1).Content })

  # Make sure current session finds uv without re-opening the shell
  $userLocalBin = Join-Path $HOME ".local\bin"
  if (-not ($env:Path -split ';' | ForEach-Object { $_.TrimEnd('\') } | Where-Object { $_ -ieq $userLocalBin })) {
    $env:Path = "$userLocalBin;$env:Path"
  }

  $uv = Get-Command uv -ErrorAction SilentlyContinue
  if (-not $uv) {
    throw "uv installation completed but 'uv' still not on PATH. Please open a new PowerShell or add $userLocalBin to PATH."
  }
  return $uv.Path
}

if ($clean) {
  Write-Host "Cleaning workspace..." -ForegroundColor Yellow
  Remove-IfExists ".venv"
  Remove-IfExists "build"
  Remove-IfExists "dist"
  Get-ChildItem -Recurse -Include "__pycache__" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
  }
  Get-ChildItem -LiteralPath . -Filter *.spec -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
  }
  Write-Host "Clean complete." -ForegroundColor Green
}

if ($build) {
  $uvPath = Ensure-Uv
  Write-Host "[1/5] Using uv at: $uvPath" -ForegroundColor Cyan

  Write-Host "[2/5] Creating uv-managed virtual environment (.venv) with CPython 3.12..." -ForegroundColor Cyan
  uv venv --python 3.12 .venv

  Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Cyan
  . .\.venv\Scripts\Activate.ps1

  Write-Host "[4/5] Syncing project dependencies with uv..." -ForegroundColor Cyan
  uv sync

  Write-Host "[5/5] Verifying interpreter..." -ForegroundColor Cyan
  python -V
  where.exe python

  Write-Host "`nSetup complete! Next steps:" -ForegroundColor Green
  Write-Host "  .\.venv\Scripts\Activate.ps1"
  Write-Host "  python app_server.py"
}

if (-not $clean -and -not $build) {
  Write-Host "Usage: .\scripts\setup.ps1 -build  or  .\scripts\setup.ps1 -clean" -ForegroundColor Yellow
  exit 1
}
