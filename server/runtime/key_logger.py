"""Utilities for capturing global hotkey sequences via NiceGUI events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger
from nicegui.events import KeyEventArguments

_MOD_ALIAS = {
    "MetaLeft": "Meta",
    "MetaRight": "Meta",
    "OSLeft": "Meta",
    "OSRight": "Meta",
    "ShiftLeft": "Shift",
    "ShiftRight": "Shift",
    "ControlLeft": "Ctrl",
    "ControlRight": "Ctrl",
    "AltLeft": "Alt",
    "AltRight": "Alt",
    "SuperLeft": "Super",
    "SuperRight": "Super",
    "Fn": "Fn",
}

_MOD_NAMES = {"Shift", "Ctrl", "Alt", "Meta", "Super", "Fn"}


def _canonical_modifiers(event: KeyEventArguments) -> List[str]:
    mods: List[str] = []
    state = getattr(event, "modifiers", None)
    if not state:
        return mods
    if getattr(state, "ctrl", False):
        mods.append("Ctrl")
    if getattr(state, "alt", False):
        mods.append("Alt")
    if getattr(state, "shift", False):
        mods.append("Shift")
    if getattr(state, "meta", False):
        mods.append("Meta")
    return mods


def _normalize_key_name(raw: str) -> str:
    name = _MOD_ALIAS.get(raw, raw)
    if name.startswith("Key") and len(name) == 4:
        return name[-1].upper()
    if name.startswith("Digit") and len(name) == 6 and name[-1].isdigit():
        return name[-1]
    if name.startswith("Numpad"):
        return "Num" + name[len("Numpad") :]
    return name


def _describe_key(event: KeyEventArguments) -> Optional[str]:
    key_obj = getattr(event, "code", None) or getattr(event, "key", None)
    if key_obj is None:
        return None
    if hasattr(key_obj, "name"):
        raw = key_obj.name
    elif hasattr(key_obj, "value"):
        raw = key_obj.value
    else:
        raw = str(key_obj)
    return _normalize_key_name(raw)


@dataclass
class KeyLogger:
    """Collect hotkey sequences from NiceGUI keyboard events."""

    modifiers: List[str] = field(default_factory=list)
    sequence: List[str] = field(default_factory=list)
    active: bool = False

    def start(self) -> None:
        self.active = True
        self.modifiers.clear()
        self.sequence.clear()
        logger.debug("Hotkey recording started")

    def stop(self) -> str:
        self.active = False
        final = self.sequence[-1] if self.sequence else ""
        logger.debug("Hotkey recording finalized: {}", final)
        return final

    def feed(self, event: KeyEventArguments) -> Optional[str]:
        if not self.active:
            return None
        action = getattr(event, "action", None)
        if getattr(action, "repeat", False):
            return None

        key_name = _describe_key(event)
        if key_name is None:
            return None

        mods = _canonical_modifiers(event)
        if key_name in _MOD_NAMES:
            for mod in mods:
                if mod not in self.modifiers:
                    self.modifiers.append(mod)
            return None

        if key_name in {"Enter", "KeyboardKey.ENTER"}:
            return self.stop()

        main = key_name.upper() if len(key_name) == 1 else key_name.title()
        pretty = "+".join(self.modifiers + [main])
        self.sequence = [pretty]
        logger.debug("Recorded hotkey combo: {}", pretty)
        return None


__all__ = ["KeyLogger"]
