"""Native NiceGUI launcher window for the packaged application."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Callable

from loguru import logger
from nicegui import app as nice_app
from nicegui import ui

from .key_logger import KeyLogger
from server.storage.file_store import FileStore


def _render_hotkey(text: str) -> str:
    parts = [f"`{segment.strip().lower()}`" for segment in text.split("+") if segment.strip()]
    return " + ".join(parts) if parts else "`f2`"


def _sanitize_port(raw: str, fallback: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    return value if 1 <= value <= 65535 else fallback


def run_launcher_ui(
    *,
    store: FileStore,
    host: str,
    port: int,
    hotkey: str,
    auto_open: bool,
    open_browser: Callable[[], None],
    request_stop: Callable[[], None],
) -> None:
    """Launch the NiceGUI native window and block until it is closed."""
    key_logger = KeyLogger()
    launcher_settings = {"host": host, "port": port, "hotkey": hotkey or "F2"}
    assets_dir = Path(__file__).resolve().parents[2] / "ui" / "assets"
    if assets_dir.exists():
        with suppress(Exception):
            nice_app.add_static_files("/ui/assets", str(assets_dir))
    else:
        logger.warning("Launcher assets directory missing: {}", assets_dir)

    @ui.page("/")
    def launcher_page() -> None:
        ui.add_head_html(
            """
            <style>
            html, body { margin:0; padding:0; background:#0f172a; color:#f8fafc; overflow:hidden; }
            </style>
            """
        )

        settings_dialog = ui.dialog()

        with settings_dialog, ui.card().classes(
            "w-[360px] max-w-[90vw] bg-slate-800 text-slate-100 p-5 flex flex-col gap-4 rounded-lg shadow-lg"
        ):
            ui.label("Server Settings").classes("text-lg font-semibold text-slate-200")
            with ui.row().classes("w-full gap-3"):
                host_input = ui.input("Host", value=str(launcher_settings["host"])).classes("flex-grow")
                port_input = (
                    ui.input("Port", value=str(launcher_settings["port"]))
                    .props("type=text inputmode=numeric pattern=\\d*")
                    .classes("w-28")
                )

            ui.label("Toggle Hotkey").classes("text-sm text-slate-300")
            hotkey_value = {"text": launcher_settings.get("hotkey", "F2")}
            hotkey_display = ui.markdown(_render_hotkey(hotkey_value["text"])).classes("text-base text-slate-100")
            record_button = ui.button("Record Hotkey").props("color=primary")
            record_status = ui.label("Current hotkey shown above").classes("text-sm text-slate-400 text-right")

            def _finalize_recording(text: str | None = None) -> None:
                key_logger.active = False
                key_logger.modifiers.clear()
                key_logger.sequence.clear()
                record_button.props("color=primary")
                record_button.text = "Record Hotkey"
                prev = hotkey_value["text"]
                if text:
                    hotkey_value["text"] = text
                hotkey_display.set_content(_render_hotkey(hotkey_value["text"]))
                if hotkey_value["text"] != prev:
                    record_status.text = f"Hotkey saved: {hotkey_value['text'].lower()}"
                else:
                    record_status.text = "Current hotkey shown above."
            def _toggle_recording() -> None:
                if key_logger.active:
                    text = key_logger.stop()
                    _finalize_recording(text or hotkey_value["text"])
                    return
                key_logger.start()
                record_status.text = "Recording... press keys (Enter to finish)"
                record_button.props("color=negative")
                record_button.text = "Stop Recording"

            record_button.on("click", _toggle_recording)

            def _handle_key(event) -> None:
                if not key_logger.active:
                    return
                result = key_logger.feed(event)
                if result is not None:
                    _finalize_recording(result or hotkey_value["text"])
                elif key_logger.sequence:
                    human = " + ".join(seg.strip().lower() for seg in key_logger.sequence[-1].split("+"))
                    record_status.text = f"Recording: {human}"

            ui.keyboard(on_key=_handle_key)

            with ui.row().classes("w-full justify-end gap-3"):
                ui.button("Cancel", on_click=lambda: ( _finalize_recording(hotkey_value["text"]), settings_dialog.close() )
                         ).props("flat color=white")

                def _save_settings() -> None:
                    new_host = (host_input.value or "").strip() or launcher_settings["host"]
                    new_port = _sanitize_port(port_input.value, launcher_settings["port"])
                    new_hotkey = hotkey_value["text"]
                    store.write_launcher_settings({"host": new_host, "port": int(new_port), "hotkey": new_hotkey})

                    msg = "Settings saved."
                    if (new_host, new_port) != (launcher_settings["host"], launcher_settings["port"]):
                        msg += " Restart required for host/port changes."

                    launcher_settings.update(host=new_host, port=new_port, hotkey=new_hotkey)
                    ui.notify(msg, type="positive", position="top-right")
                    settings_dialog.close()

                ui.button("Save", on_click=_save_settings).props("color=primary")

        with ui.column().classes("w-full h-screen bg-slate-900 text-slate-100 flex items-center justify-center"):
            with ui.column().classes("w-[680px] max-w-[92vw] gap-6 p-6 mb-12 box-border"):
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.row().classes("items-center gap-3"):
                        ui.image("/ui/assets/favicon.png").classes("w-[42px] h-[42px] rounded-xl bg-slate-800")
                        ui.label("Custom Gamepad Viewer").classes("text-2xl font-semibold text-white whitespace-nowrap")
                    ui.button(icon="settings", on_click=settings_dialog.open).props("flat color=white").tooltip("Settings")

                with ui.card().classes(
                    "w-full h-[320px] bg-slate-800 text-slate-100 rounded-xl shadow-lg flex flex-col items-center justify-center gap-4"
                ):
                    ui.label(
                        f"Server running on http://{launcher_settings['host']}:{launcher_settings['port']}"
                    ).classes("text-sm text-slate-300")
                    ui.button("Open Viewer", on_click=open_browser).props("color=primary")

                    def _quit_server() -> None:
                        ui.notify("Stopping server…", position="top")
                        request_stop()
                        with suppress(Exception):
                            nice_app.native.main_window.close()  # type: ignore[attr-defined]
                        ui.shutdown()

                    ui.button("Quit Server", on_click=_quit_server).props("color=negative")

        # Do NOT call launcher_page() here; the decorator registers it.
        if auto_open:
            ui.timer(0.75, open_browser, once=True)

    ui.run(
        native=True,
        reload=False,
        host="127.0.0.1",
        port=8083,
        title="Custom Gamepad Viewer",
        window_size=(700, 500),
        fullscreen=False,
        frameless=False,
        dark=True,
    )
