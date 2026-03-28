"""Simulate a realistic Claude session for demo recording.

Writes a sequence of state updates to a demo session, with timed
transitions that look like a real coding session. Run this in one
terminal while recording the viewer in another.

Usage:
    uv run python demo/simulate-session.py
"""

import json
import os
import tempfile
import time
from pathlib import Path

PANEL_DIR = Path.home() / ".claude-panel"
DEMO_SESSION = "demo-recording"
STATE_DIR = PANEL_DIR / "sessions" / DEMO_SESSION
STATE_FILE = STATE_DIR / "state.json"
ACTIVE_FILE = PANEL_DIR / "active_session"
SCREENSAVERS_DIR = PANEL_DIR / "screensavers"


def write_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["ts"] = time.time()
    fd, tmp = tempfile.mkstemp(dir=str(STATE_DIR), suffix=".tmp")
    with open(fd, "w") as f:
        json.dump(state, f)
    os.rename(tmp, str(STATE_FILE))
    ACTIVE_FILE.write_text(DEMO_SESSION)


def mood(emoji: str, context: str, tip: str = "") -> dict:
    """Build a mood screen state."""
    # Try to load custom emoji art
    from claude_panel.constants import EMOJI_DIR
    EMOJI_MAP = {
        "\U0001f525": "fire", "\U0001f914": "thinking", "\U0001f3af": "target",
        "\U0001f389": "celebration", "\U0001f3d7\ufe0f": "building",
        "\U0001f41b": "bug", "\U0001f4a1": "lightbulb", "\u2615": "coffee",
        "\u26a1": "urgent", "\U0001f9ea": "testing", "\U0001f3a8": "designing",
        "\U0001f4da": "learning", "\U0001f680": "rocket", "\U0001f527": "refactoring",
    }
    art_name = EMOJI_MAP.get(emoji, "")
    script_path = EMOJI_DIR / f"{art_name}.py" if art_name else None

    if script_path and script_path.exists():
        code = script_path.read_text()
    else:
        code = f"""
from rich.text import Text
from rich.align import Align
canvas.write(Text(""))
canvas.write(Text(""))
canvas.write(Align.center(Text("{emoji}", style="bold")))
canvas.write(Text(""))
canvas.write(Align.center(Text("\u2501" * 40, style="dim")))
canvas.write(Text(""))
canvas.write(Align.center(Text(CONTEXT, style="bold")))
if TIP:
    canvas.write(Text(""))
    canvas.write(Align.center(Text(TIP, style="dim italic")))
"""
    header = f"CONTEXT = {context!r}\nTIP = {tip!r}\n"
    return {
        "mode": "multi",
        "screens": {
            "main": {"type": "mood", "code": header + code, "emoji": emoji, "context": context},
        },
        "screen_order": ["main", "status", "ambient"],
        "active": "main",
    }


def add_status(state: dict, task: str, files: str, decisions: str) -> dict:
    state["screens"]["status"] = {
        "type": "sections",
        "sections": [
            {"id": "task", "title": "Current Task", "content": task},
            {"id": "files", "title": "Files Changed", "content": files},
            {"id": "decisions", "title": "Decisions", "content": decisions},
        ],
    }
    return state


def add_ambient(state: dict, name: str = "tokyo-drift") -> dict:
    ss_path = SCREENSAVERS_DIR / f"{name}.py"
    if ss_path.exists():
        state["screens"]["ambient"] = {
            "type": "screensaver",
            "name": name,
            "code": ss_path.read_text(),
        }
    return state


def add_main_sections(state: dict, sections: list[dict]) -> dict:
    state["screens"]["main"] = {"type": "sections", "sections": sections}
    state["active"] = "main"
    return state


# ── Scene sequence ──────────────────────────────────────────────

def run():
    print("Starting demo simulation...")
    print("Switch to the viewer terminal and watch the panel update.")
    print()

    # Scene 1: Starting up — thinking mood
    print("[1/6] Thinking...")
    state = mood("\U0001f914", "Reading the codebase...", "Getting oriented")
    state = add_status(state, "*Exploring project structure*", "*None yet*", "*None yet*")
    state = add_ambient(state, "tokyo-drift")
    write_state(state)
    time.sleep(4)

    # Scene 2: Found something — focused
    print("[2/6] Focused on task...")
    state = mood("\U0001f3af", "Adding session isolation", "Key files: session.py, curator.py, viewer.py")
    state = add_status(state,
        "Add per-session state isolation for multi-session support",
        "- `session.py` \u2014 new module for session identification\n- `curator.py` \u2014 session-aware read/write\n- `viewer.py` \u2014 active session polling",
        "- Per-session state files over shared global state\n- Process tree walking to resolve session ID",
    )
    state = add_ambient(state, "tokyo-drift")
    write_state(state)
    time.sleep(4)

    # Scene 3: Making progress — rich content on main
    print("[3/6] Showing rich content...")
    state["active"] = "main"
    state = add_main_sections(state, [
        {
            "id": "what-changed",
            "title": "\U0001f525 What Changed",
            "content": (
                "New `session.py` module resolves Claude Code session ID:\n\n"
                "```python\n"
                "def get_session_id() -> str | None:\n"
                "    claude_pid = _find_claude_pid()\n"
                "    return get_session_id_from_pid(claude_pid)\n"
                "```\n\n"
                "State now writes to `~/.claude-panel/sessions/<uuid>/`"
            ),
        },
        {
            "id": "next",
            "title": "Next Steps",
            "content": "- [x] Create session.py\n- [x] Update curator.py\n- [x] Update viewer.py\n- [ ] Update hook scripts\n- [ ] Test with multiple sessions",
        },
    ])
    state = add_status(state,
        "Add per-session state isolation for multi-session support",
        "- `session.py` \u2014 session identification\n- `curator.py` \u2014 session-aware state\n- `viewer.py` \u2014 active session polling\n- `server.py` \u2014 cached session resolution",
        "- Per-session state files over shared global state\n- Process tree walking to resolve session ID\n- Atomic writes with active_session tracking",
    )
    state = add_ambient(state, "tokyo-drift")
    write_state(state)
    time.sleep(5)

    # Scene 4: Done! Celebration
    print("[4/6] Celebration...")
    state = mood("\U0001f389", "Session isolation complete!", "All tests passing \u2014 ready to commit")
    state = add_status(state,
        "Session isolation \u2014 done!",
        "- `session.py` \u2014 session identification\n- `curator.py` \u2014 session-aware state\n- `viewer.py` \u2014 active session polling\n- `server.py` \u2014 cached session resolution\n- `curator.sh` / `session-start.sh` / `nudge.sh` \u2014 per-session hooks",
        "- Per-session state files\n- Process tree for session ID\n- Backward-compatible with global fallback",
    )
    state = add_ambient(state, "tokyo-drift")
    write_state(state)
    time.sleep(4)

    # Scene 5: Switch to status screen
    print("[5/6] Status screen...")
    state["active"] = "status"
    write_state(state)
    time.sleep(4)

    # Scene 6: Switch to ambient
    print("[6/6] Ambient screensaver...")
    state["active"] = "ambient"
    write_state(state)
    time.sleep(6)

    print("\nDone! Clean up with: rm -rf ~/.claude-panel/sessions/demo-recording")


if __name__ == "__main__":
    run()
