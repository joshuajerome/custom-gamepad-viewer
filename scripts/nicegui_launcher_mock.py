"""Standalone NiceGUI mock of the Custom Gamepad Viewer launcher UI.

Run via:
    uv run python launcher.py
"""

from __future__ import annotations

from contextlib import suppress

from loguru import logger
from nicegui import app, ui

from server.runtime.key_logger import KeyLogger


# ---- UI helpers --------------------------------------------------------------

def _attach_assets() -> None:
    with suppress(Exception):
        app.add_static_files("/assets", "ui/assets")


def _build_settings_dialog() -> ui.dialog:
    dialog = ui.dialog()
    key_logger = KeyLogger()

    with dialog, ui.card().classes(
        "w-[360px] max-w-[90vw] bg-slate-800 text-slate-100 p-5 flex flex-col gap-4 rounded-lg shadow-lg"
    ):
        ui.label("Server Settings").classes("text-lg font-semibold text-slate-200")
        with ui.row().classes("w-full gap-3"):
            host_input = ui.input("Host", value="127.0.0.1").classes("flex-grow")
            port_input = ui.input("Port", value="8000").props("type=text inputmode=numeric pattern=\\d*").classes("w-28")

        ui.label("Toggle Hotkey").classes("text-sm text-slate-300")
        hotkey_value = {"text": "F2"}
        hotkey_display = ui.markdown("`F2`").classes("text-base text-slate-100")
        record_button = ui.button("Record Hotkey").props("color=primary")
        record_status = ui.label("Current hotkey shown above.").classes("text-sm text-slate-400 text-right")

        def _render_hotkey(text: str) -> str:
            parts = [f"`{segment.strip().lower()}`" for segment in text.split("+") if segment.strip()]
            return " + ".join(parts) if parts else "`F2`"

        def _finalize_recording(text: str | None = None) -> None:
            key_logger.active = False
            key_logger.modifiers.clear()
            key_logger.sequence.clear()
            record_button.props("color=primary")
            record_button.text = "Record Hotkey"
            if text:
                hotkey_value["text"] = text
            rendered = _render_hotkey(hotkey_value["text"])
            hotkey_display.set_content(rendered)
            record_status.text = f"Hotkey saved: {rendered.replace('`', '')}"

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
                human = " + ".join(part.strip().lower() for part in key_logger.sequence[-1].split("+"))
                record_status.text = f"Recording: {human}"

        ui.keyboard(on_key=_handle_key)

        with ui.row().classes("w-full justify-end gap-3"):
            def _cancel_settings() -> None:
                _finalize_recording(hotkey_value["text"])
                dialog.close()

            ui.button("Cancel", on_click=_cancel_settings).props("flat color=white")

            def _save_settings() -> None:
                logger.info(
                    "Saving settings host={}, port={}, hotkey={}",
                    host_input.value,
                    port_input.value,
                    hotkey_value["text"],
                )
                ui.notify(
                    f"Saved host={host_input.value}, port={port_input.value}, hotkey={hotkey_value['text']}",
                    type="positive",
                    position="bottom",
                )
                dialog.close()

            ui.button("Save", on_click=_save_settings).props("color=primary")
        hotkey_display.set_content(_render_hotkey(hotkey_value["text"]))

    return dialog


# ---- Page --------------------------------------------------------------------

@ui.page("/")
def launcher_page() -> None:
    ui.add_head_html(
        """
        <style>
        html, body { margin:0; padding:0; background:#0f172a; color:#f8fafc; overflow:hidden; }
        </style>
        """
    )

    settings_dialog = _build_settings_dialog()

    with ui.column().classes("w-full h-screen bg-slate-900 text-slate-100 flex items-center justify-center overflow-hidden"):
        with ui.column().classes("w-[680px] max-w-[92vw] gap-6 p-6 mb-12 box-border"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-3"):
                    ui.image("/assets/favicon.png").classes("w-[42px] h-[42px] rounded-xl bg-slate-800")
                    ui.label("Custom Gamepad Viewer").classes("text-2xl font-semibold text-white whitespace-nowrap")

                ui.button(icon="settings", on_click=settings_dialog.open).props("flat color=white").tooltip("Settings")

            with ui.card().classes(
                "w-full h-[320px] bg-slate-800 text-slate-100 rounded-xl shadow-lg flex items-center justify-center"
            ):
                ui.label("Main content").classes("text-sm tracking-wide text-slate-300")


# ---- Entry point -------------------------------------------------------------

def main() -> None:
    _attach_assets()

    ui.run(
        native=True,
        reload=False,
        host="127.0.0.1",
        port=8082,
        title="Custom Gamepad Viewer",
        window_size=(700, 500),
        fullscreen=False,
        frameless=False,
        dark=True,
    )


if __name__ == "__main__":
    main()
