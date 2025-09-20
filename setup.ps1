param(
    [switch]$clean,
    [switch]$build
)

Set-Location -LiteralPath $PSScriptRoot

function Remove-IfExists {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed $Path"
    }
}

# ---------------------------
# CLEAN STEP
# ---------------------------
if ($clean) {
    Write-Host "Cleaning workspace..." -ForegroundColor Yellow

    # Deactivate and strip venv PATH if active
    if ($env:VIRTUAL_ENV -and (Test-Path $env:VIRTUAL_ENV)) {
        Write-Host "  Deactivating active virtual environment..." -ForegroundColor Yellow
        if (Get-Command deactivate -ErrorAction SilentlyContinue) {
            deactivate
        }
        Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
        $env:PATH = ($env:PATH -split ';' | Where-Object { $_ -notlike "*\.venv*" }) -join ';'
    }

    # Project-specific removals
    Remove-IfExists ".venv"
    Remove-IfExists "tmp\slot.json"
    Remove-IfExists "build"
    Remove-IfExists "dist"

    # Remove any PyInstaller spec files at repo root (e.g., local-gamepad-viewer.spec)
    Get-ChildItem -LiteralPath . -Filter *.spec -File -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed $($_.Name)"
    }

    # Purge __pycache__ everywhere
    Get-ChildItem -Recurse -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq "__pycache__" } |
        ForEach-Object {
            Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  Removed $($_.FullName)"
        }

    # Example leftover path from your original script; keep if relevant
    Remove-IfExists "containers\dockerfiles\buildtime"

    Write-Host "Clean complete.`n" -ForegroundColor Green
}

# ---------------------------
# BUILD STEP
# ---------------------------
if ($build) {
    Write-Host "[1/4] Creating Python virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv

    Write-Host "[2/4] Activating virtual environment..." -ForegroundColor Cyan
    . .\.venv\Scripts\Activate.ps1

    Write-Host "[3/4] Installing uv..." -ForegroundColor Cyan
    pip install uv

    Write-Host "[4/4] Initializing uv project..." -ForegroundColor Cyan
    uv sync

    Write-Host "`nEnvironment setup complete!" -ForegroundColor Green
}

# ---------------------------
# HELP
# ---------------------------
if (-not $clean -and -not $build) {
    Write-Host "Usage: .\setup.ps1 -clean [-build]  or  .\setup.ps1 -build" -ForegroundColor Yellow
    exit 1
}
