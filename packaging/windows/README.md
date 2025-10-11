Place your Windows ICO here as `CustomGamepadViewer.ico`.

Recommended sizes embedded in one multi-size ICO: 256, 128, 96, 64, 48, 40, 32, 24, 20, 16.

This icon is used for:
- The EXE file icon (PyInstaller `--icon`)
- The runtime taskbar/console/Tk window icon (loaded at startup)

If this file is missing, Windows build will still succeed, but the EXE/taskbar may show a default icon.

Note on NiceGUI packaging:
- If you build the EXE locally with PyInstaller, include NiceGUI package data so the native window works:
  - Example: `pyinstaller --noconfirm --clean --noupx --onedir --name CustomGamepadViewer --icon packaging\windows\CustomGamepadViewer.ico --add-data "ui;ui" --add-data "controller_css;controller_css" --add-data "server/static;server/static" --add-data "themes;themes" --collect-all nicegui app.py`
  - Without `--collect-all nicegui`, NiceGUI may fail to load internal assets (e.g., `nicegui/static/sad_face.svg`) when running the EXE.
