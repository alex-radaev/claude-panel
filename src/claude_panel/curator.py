"""Panel curator — state-writing helpers for background agents.

The curator is a background agent spawned by main Claude after each response.
It has full tool access (WebSearch, Read, etc.) and its work is hidden from
the conversation. This module provides the helpers for writing panel state.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from typing import Any

from claude_panel.constants import (
    PANEL_DIR,
    SCREENSAVERS_DIR,
    STATE_FILE,
)

STANDARD_ORDER = ["main", "status", "ambient"]

STATUS_SECTIONS = [
    {"id": "task", "title": "Current Task", "content": "*Not set*"},
    {"id": "files", "title": "Files Changed", "content": "*None yet*"},
    {"id": "decisions", "title": "Decisions", "content": "*None yet*"},
]


def read_state() -> dict[str, Any]:
    """Read current panel state."""
    if not STATE_FILE.exists():
        return {}
    try:
        raw = STATE_FILE.read_text()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def write_state(state: dict[str, Any]) -> None:
    """Atomically write state to state.json, clearing loading flag."""
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    state.pop("loading", None)
    state.pop("loading_message", None)
    state["ts"] = time.time()

    fd, tmp_path = tempfile.mkstemp(dir=str(PANEL_DIR), suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(state, f)
        os.rename(tmp_path, str(STATE_FILE))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def ensure_multi(state: dict[str, Any]) -> dict[str, Any]:
    """Ensure state is in multi-screen mode."""
    if state.get("mode") == "multi":
        return state
    return {"mode": "multi", "screens": {}, "screen_order": [], "active": None}


def ensure_screen_order(order: list[str]) -> list[str]:
    """Standard screens first, custom screens after."""
    standard = [s for s in STANDARD_ORDER if s in order]
    custom = [s for s in order if s not in STANDARD_ORDER]
    return standard + custom


def update_main(state: dict[str, Any], sections: list[dict[str, str]]) -> dict[str, Any]:
    """Replace main screen content and show it."""
    state = ensure_multi(state)
    screens = state.get("screens", {})
    order = list(state.get("screen_order", []))
    screens["main"] = {"type": "sections", "sections": sections}
    if "main" not in order:
        order.append("main")
    state["screens"] = screens
    state["screen_order"] = ensure_screen_order(order)
    state["active"] = "main"
    return state


def update_status_section(state: dict[str, Any], section_id: str, content: str) -> dict[str, Any]:
    """Update a single section on the status screen."""
    state = ensure_multi(state)
    screens = state.get("screens", {})
    order = list(state.get("screen_order", []))

    status_screen = screens.get("status")
    if status_screen is None or status_screen.get("type") != "sections":
        status_screen = {"type": "sections", "sections": [dict(s) for s in STATUS_SECTIONS]}

    existing = status_screen.get("sections", [])
    found = False
    for s in existing:
        if s.get("id") == section_id:
            s["content"] = content
            found = True
            break
    if not found:
        title = section_id.replace("_", " ").replace("-", " ").title()
        existing.append({"id": section_id, "title": title, "content": content})

    status_screen["sections"] = existing
    screens["status"] = status_screen
    if "status" not in order:
        order.append("status")
    state["screens"] = screens
    state["screen_order"] = ensure_screen_order(order)
    return state


def set_active(state: dict[str, Any], screen: str) -> dict[str, Any]:
    """Switch the active screen."""
    if screen in state.get("screens", {}):
        state["active"] = screen
    return state
