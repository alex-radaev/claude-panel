"""MCP server exposing panel tools with 3-screen model: main + status + ambient."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from typing import Any

from fastmcp import FastMCP

from claude_panel.constants import CONTENT_DIR, PANEL_DIR, SCREENSAVERS_DIR, STATE_FILE

# ── Standard screen ordering ──
# main is Claude's free-form display, status is the structured dashboard,
# ambient is the screensaver. Custom screens go after these.
STANDARD_ORDER = ["main", "status", "ambient"]


mcp = FastMCP(
    "claude-panel",
    instructions="""\
You have a persistent side panel. The **main screen is yours** — use it to express \
what's happening, show context, and communicate non-verbally with the user.

## Express yourself on the main screen (DO THIS)

After each meaningful response, spawn a background agent to update the main screen. \
Pick an emoji that matches the vibe, add context, and optionally a tip:

```python
Agent(
    description="Update panel",
    mode="bypassPermissions",
    run_in_background=True,
    prompt=\"\"\"Run this bash command:
cd /Users/aradaev/Desktop/Projects/claude-panel && uv run python3 -c "
from claude_panel.curator import read_state, write_state, update_mood
state = read_state()
state = update_mood(state, 'EMOJI', 'CONTEXT', 'TIP')
write_state(state)
"\"\"\"
)
```

### Emoji vocabulary

| Emoji | Mood | Use when... |
|-------|------|-------------|
| 🔥 | On fire | Making fast progress, things are clicking |
| 🤔 | Thinking | Investigating, debugging, exploring |
| 🎯 | Focused | Clear goal, executing methodically |
| 🎉 | Celebration | Just completed something, milestone |
| 🏗️ | Building | Writing new code, creating |
| 🐛 | Bug hunt | Fixing issues, chasing errors |
| 💡 | Insight | Discovered something, had an idea |
| ☕ | Chill | Idle, casual conversation |
| ⚡ | Urgent | Time-sensitive, important fix |
| 🧪 | Testing | Running tests, verifying |
| 🎨 | Designing | Architecture, planning, creative work |
| 📚 | Learning | Reading docs, exploring codebase |
| 🚀 | Shipping | Committing, pushing, deploying |
| 🔧 | Refactoring | Cleaning up, improving code |

### Examples

```python
# Just started a task
update_mood(state, '🎯', 'Adding user authentication', 'Key files: auth.py, routes.py')

# Making progress
update_mood(state, '🔥', 'Auth middleware working', '3 of 5 steps done')

# Hit a bug
update_mood(state, '🐛', 'Token validation failing on refresh', 'Checking expiry logic')

# Finished!
update_mood(state, '🎉', 'Auth complete — all tests passing', 'Ready to commit')

# Idle
update_mood(state, '☕', 'Waiting for next task', '')
```

### When to update main
- When the **mood changes** — new task, progress, blocker, completion
- When you want to **show something** — diagram, concept, key info
- **Not every message** — only when something meaningful shifted

### Rich content on main

For bigger content (explanations, diagrams, docs), use `update_main()` with full sections:
```python
update_main(state, [
    {'id': 'diagram', 'title': 'Architecture', 'content': '...'},
    {'id': 'notes', 'title': 'Key Points', 'content': '...'},
])
```

Or spawn a Sonnet agent to fetch external docs:
```python
Agent(description="Fetch docs for panel", mode="bypassPermissions",
      run_in_background=True, prompt="Fetch [URL], write to panel...")
```

## Status screen (automatic)

The status screen auto-updates via a Stop hook — you don't need to manage it. \
It shows: current task, files changed, decisions made.

## Quick commands (direct tool calls)

- `panel(show="ambient")` — screensaver
- `panel(show="main")` — switch to main
- `panel(screensaver="rain-city")` — change screensaver
""",
)

# ── State helpers ───────────────────────────────────────────────────


def _read_state() -> dict[str, Any]:
    """Read current state from the shared JSON file."""
    if not STATE_FILE.exists():
        return {}
    try:
        raw = STATE_FILE.read_text()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_state(data: dict[str, Any]) -> None:
    """Atomically write state to the shared JSON file."""
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    data["ts"] = time.time()

    fd, tmp_path = tempfile.mkstemp(dir=PANEL_DIR, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(data, f)
        import os
        os.rename(tmp_path, STATE_FILE)
    except BaseException:
        import os
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _ensure_multi(state: dict[str, Any]) -> dict[str, Any]:
    """Ensure state is in multi-screen mode, migrating if needed."""
    if state.get("mode") == "multi":
        return state
    return {"mode": "multi", "screens": {}, "screen_order": [], "active": None}


def _ensure_screen_order(order: list[str]) -> list[str]:
    """Ensure standard screens come first in the expected order."""
    # Pull out standard screens that exist
    standard = [s for s in STANDARD_ORDER if s in order]
    custom = [s for s in order if s not in STANDARD_ORDER]
    return standard + custom


# Default sections for the status screen
STATUS_SECTIONS = [
    {"id": "task", "title": "Current Task", "content": "*Not set*"},
    {"id": "files", "title": "Files Changed", "content": "*None yet*"},
    {"id": "decisions", "title": "Decisions", "content": "*None yet*"},
]


# ── Panel tools ─────────────────────────────────────────────────────


def _parse_markdown_to_sections(text: str) -> list[dict[str, str]]:
    """Parse markdown with ## headers into panel sections."""
    sections: list[dict[str, str]] = []
    current_title: str | None = None
    current_id: str | None = None
    current_lines: list[str] = []
    # Content before any heading
    preamble_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            # Save previous section
            if current_title is not None:
                sections.append({
                    "id": current_id or "unknown",
                    "title": current_title,
                    "content": "\n".join(current_lines).strip(),
                })
            elif preamble_lines:
                # Content before first heading becomes a section
                joined = "\n".join(preamble_lines).strip()
                if joined:
                    sections.append({
                        "id": "intro",
                        "title": "Overview",
                        "content": joined,
                    })

            current_title = line[3:].strip()
            import re
            current_id = re.sub(r"[^a-z0-9_-]", "", current_title.lower().replace(" ", "-"))
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
        else:
            preamble_lines.append(line)

    # Save last section
    if current_title is not None:
        sections.append({
            "id": current_id or "unknown",
            "title": current_title,
            "content": "\n".join(current_lines).strip(),
        })
    elif preamble_lines:
        joined = "\n".join(preamble_lines).strip()
        if joined:
            sections.append({
                "id": "content",
                "title": "Content",
                "content": joined,
            })

    return sections


@mcp.tool()
async def panel(
    sections: list[dict[str, str]] | None = None,
    screen: str | None = None,
    section: str | None = None,
    content: str | None = None,
    file: str | None = None,
    screensaver: str | None = None,
    show: str | None = None,
    clear: str | None = None,
) -> str:
    """Manage the panel's three screens: main (free-form), status (structured), ambient (screensaver).

    Args:
        sections: List of section dicts with id, title, content (markdown).
                  Updates the "main" screen by default, or a named screen if `screen` is set.
        screen: Target screen name. Defaults to "main" for sections.
        section: Update a single section by ID on a screen (use with `content`).
                 Most useful for status: panel(screen="status", section="files", content="...")
        content: New content for the section specified by `section`.
        file: Load a screen from a markdown file in ~/.claude-panel/content/.
              Use ## headings to define sections. Defaults to "main" screen.
              Write the file first, then call panel(file="main.md") — keeps conversation clean.
        screensaver: Set up the ambient screen with a saved screensaver name.
        show: Switch the visible screen (e.g., "ambient", "status", "main").
        clear: Remove a custom screen by name. Cannot clear standard screens.

    Common patterns:
      panel(file="main.md")                                          # load from file, show it
      panel(screen="status", section="files", content="- server.py") # update one status section
      panel(screensaver="tokyo-drift")                               # set up ambient
      panel(show="ambient")                                          # switch to screensaver
    """
    state = _read_state()

    # ── Handle clear ──
    if clear is not None:
        if clear in STANDARD_ORDER:
            return f"Cannot clear standard screen '{clear}'. Use panel(screen='{clear}', sections=[...]) to update it instead."
        if state.get("mode") != "multi" or "screens" not in state:
            return f"No screen '{clear}' to remove."
        screens = state.get("screens", {})
        order = state.get("screen_order", [])
        if clear not in screens:
            return f"Screen '{clear}' not found. Available: {', '.join(order) or 'none'}"
        del screens[clear]
        order = [s for s in order if s != clear]
        state["screens"] = screens
        state["screen_order"] = order
        if state.get("active") == clear:
            state["active"] = order[0] if order else None
        _write_state(state)
        return f"Screen '{clear}' removed. Showing: {state.get('active')}"

    # ── Handle show (switch active screen) ──
    if show is not None:
        if state.get("mode") != "multi":
            return f"No screens yet. Use panel(sections=[...]) to get started."
        if show not in state.get("screens", {}):
            avail = ", ".join(state.get("screen_order", []))
            return f"Screen '{show}' not found. Available: {avail or 'none'}"
        state["active"] = show
        _write_state(state)
        return f"Showing screen '{show}'."

    # ── Handle screensaver (ambient screen) ──
    if screensaver is not None:
        target = screen if screen is not None else "ambient"
        path = SCREENSAVERS_DIR / f"{screensaver}.py"
        if not path.exists():
            available = [p.stem for p in SCREENSAVERS_DIR.glob("*.py")] if SCREENSAVERS_DIR.exists() else []
            return f"Screensaver '{screensaver}' not found. Available: {', '.join(available) or 'none'}"
        code = path.read_text()
        state = _ensure_multi(state)
        screens = state.get("screens", {})
        order = state.get("screen_order", [])
        screens[target] = {"type": "screensaver", "name": screensaver, "code": code}
        if target not in order:
            order.append(target)
        state["screens"] = screens
        state["screen_order"] = _ensure_screen_order(order)
        # Don't auto-show ambient — keep current view
        if not state.get("active"):
            state["active"] = target
        _write_state(state)
        return f"Ambient screen set to screensaver '{screensaver}'."

    # ── Handle single section update (incremental) ──
    if section is not None and content is not None:
        target = screen if screen is not None else "status"
        state = _ensure_multi(state)
        screens = state.get("screens", {})
        order = state.get("screen_order", [])

        # Get or initialize the target screen
        screen_data = screens.get(target)
        if screen_data is None or screen_data.get("type") != "sections":
            # Initialize status with default sections, others with empty
            if target == "status":
                screen_data = {"type": "sections", "sections": [dict(s) for s in STATUS_SECTIONS]}
            else:
                screen_data = {"type": "sections", "sections": []}

        # Find and update or append the section
        existing = screen_data.get("sections", [])
        found = False
        for s in existing:
            if s.get("id") == section:
                s["content"] = content
                found = True
                break
        if not found:
            # Auto-title from section ID
            title = section.replace("_", " ").replace("-", " ").title()
            existing.append({"id": section, "title": title, "content": content})
        screen_data["sections"] = existing

        screens[target] = screen_data
        if target not in order:
            order.append(target)
        state["screens"] = screens
        state["screen_order"] = _ensure_screen_order(order)
        # Don't auto-switch when updating status — stay on current screen
        if not state.get("active"):
            state["active"] = target
        _write_state(state)
        return f"Updated '{section}' on {target} screen."

    # ── Handle file-based update ──
    if file is not None:
        target = screen if screen is not None else "main"
        file_path = CONTENT_DIR / file
        if not file_path.exists():
            return f"File not found: {file_path}"
        text = file_path.read_text()
        parsed = _parse_markdown_to_sections(text)
        if not parsed:
            return f"No content found in {file}."
        state = _ensure_multi(state)
        screens = state.get("screens", {})
        order = state.get("screen_order", [])
        screens[target] = {"type": "file", "file": file, "sections": parsed}
        if target not in order:
            order.append(target)
        state["screens"] = screens
        state["screen_order"] = _ensure_screen_order(order)
        state["active"] = target
        _write_state(state)
        n = len(order)
        label = "Main screen" if target == "main" else f"Screen '{target}'"
        return f"{label} loaded from {file} ({len(parsed)} sections). {n} screen{'s' if n != 1 else ''} total."

    # ── Handle full sections update ──
    if sections is not None:
        target = screen if screen is not None else "main"
        state = _ensure_multi(state)
        screens = state.get("screens", {})
        order = state.get("screen_order", [])
        screens[target] = {"type": "sections", "sections": sections}
        if target not in order:
            order.append(target)
        state["screens"] = screens
        state["screen_order"] = _ensure_screen_order(order)
        # Auto-show when updating main or a named screen
        state["active"] = target
        _write_state(state)
        n = len(order)
        label = "Main screen" if target == "main" else f"Screen '{target}'"
        return f"{label} updated ({len(sections)} sections) and shown. {n} screen{'s' if n != 1 else ''} total."

    return "Nothing to update. Pass sections, section+content, screensaver, show, or clear."


@mcp.tool()
async def panel_script(code: str, title: str = "Animation") -> str:
    """Run a Python script in the panel viewer for animated/dynamic content.

    This replaces all screens with a one-off animation. Use screensaver screens
    (via panel(screensaver=...)) for persistent ambient animations.

    The script executes inside the Textual viewer and receives:
      - canvas: a RichLog widget -- call canvas.write(...) to display content
      - sleep: an async sleep function for timing animations
      - width: int -- available width in characters
      - height: int -- available height in lines
      - Rich library classes: Text, Panel, Table, Columns, Syntax, etc.
    """
    _write_state({"mode": "script", "script": {"code": code, "title": title}})
    return f"Script '{title}' sent to panel viewer."


@mcp.tool()
async def screensaver_save(name: str, code: str) -> str:
    """Save a screensaver animation script.

    The code should represent one cycle of the animation. The viewer will
    loop it continuously. The script receives the same namespace as panel_script:
    canvas, sleep, width, height, Text, Panel, Table, etc.

    Write the code as a single pass -- the viewer wraps it in a loop.
    """
    SCREENSAVERS_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSAVERS_DIR / f"{name}.py"
    path.write_text(code)
    return f"Screensaver '{name}' saved."


@mcp.tool()
async def screensaver_play(name: str) -> str:
    """Play a saved screensaver by name. Loops until interrupted.

    Prefer panel(screensaver=NAME) to make it the ambient screen.
    """
    path = SCREENSAVERS_DIR / f"{name}.py"
    if not path.exists():
        available = [p.stem for p in SCREENSAVERS_DIR.glob("*.py")] if SCREENSAVERS_DIR.exists() else []
        return f"Screensaver '{name}' not found. Available: {', '.join(available) or 'none'}"

    code = path.read_text()
    _write_state({"mode": "screensaver", "screensaver": {"name": name, "code": code}})
    return f"Screensaver '{name}' playing."


@mcp.tool()
async def screensaver_list() -> str:
    """List all saved screensavers."""
    if not SCREENSAVERS_DIR.exists():
        return "No screensavers saved yet."

    names = sorted(p.stem for p in SCREENSAVERS_DIR.glob("*.py"))
    if not names:
        return "No screensavers saved yet."

    return f"Available screensavers: {', '.join(names)}"


OPEN_APPLESCRIPT = """
tell application "iTerm2"
    tell current session of current tab of current window
        set newSession to (split vertically with default profile)
        tell newSession
            write text "cd {project_dir} && uv run claude-panel"
        end tell
    end tell
end tell
"""


@mcp.tool()
async def panel_open() -> str:
    """Open the panel viewer in an iTerm2 vertical split pane.

    Creates a new vertical split in the current iTerm2 window and starts
    the Textual viewer. Call this before using panel() or panel_script().
    """
    project_dir = str(PANEL_DIR.parent / "Desktop" / "Projects" / "claude-panel")
    import importlib.util
    spec = importlib.util.find_spec("claude_panel")
    if spec and spec.origin:
        from pathlib import Path
        project_dir = str(Path(spec.origin).parent.parent.parent)

    script = OPEN_APPLESCRIPT.format(project_dir=project_dir)
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return "Panel viewer opened in iTerm2 split pane."
    except subprocess.CalledProcessError as e:
        return f"Failed to open panel: {e.stderr.decode()}"
    except FileNotFoundError:
        return "osascript not found -- panel_open() only works on macOS with iTerm2."


def main():
    mcp.run()


if __name__ == "__main__":
    main()
