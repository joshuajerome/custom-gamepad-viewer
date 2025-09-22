# Local Gamepad Viewer — Phase 0

Bootstrap dev environment (FastAPI + placeholder HTML UI).

## Prereqs
- Python 3.12+
- Windows: PowerShell; macOS/Linux: bash/zsh
- (Optional) [uv](https://github.com/astral-sh/uv)

## One-time setup

### Windows
```powershell
.\scripts\setup.ps1 -build
```

### MacOS/Linux
chmod +x scripts/setup.sh
./scripts/setup.sh --build

### Run the dev server
# within the venv
python app_server.py
