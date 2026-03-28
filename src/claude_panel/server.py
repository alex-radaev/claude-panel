"""MCP server exposing panel() and panel_script() tools."""

from __future__ import annotations

import json
import tempfile
import time
from typing import Any

from fastmcp import FastMCP

from claude_panel.constants import PANEL_DIR, SCREENSAVERS_DIR, STATE_FILE

mcp = FastMCP(
    "claude-panel",
    instructions=(
        "Use the panel() tool to show persistent context to the user in a side panel. "
        "Use panel_script() to run animated or dynamic visualizations."
    ),
)


def _write_state(data: dict[str, Any]) -> None:
    """Atomically write state to the shared JSON file."""
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    data["ts"] = time.time()

    # Atomic write: temp file + rename
    fd, tmp_path = tempfile.mkstemp(dir=PANEL_DIR, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(data, f)
        # os.rename is atomic on the same filesystem
        import os
        os.rename(tmp_path, STATE_FILE)
    except BaseException:
        import os
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


@mcp.tool()
async def panel(sections: list[dict[str, str]]) -> str:
    """Update the context panel with static content.

    Each section is a dict with:
      - id: unique identifier (e.g. "goal", "progress", "assumptions")
      - title: display title
      - content: markdown string (supports headers, lists, checkboxes, code blocks)

    Pass an empty list to clear the panel.

    Example:
      panel(sections=[
        {"id": "goal", "title": "Goal", "content": "Build auth middleware"},
        {"id": "progress", "title": "Progress", "content": "- [x] Read code\\n- [ ] Write tests"},
      ])
    """
    _write_state({"mode": "sections", "sections": sections})
    n = len(sections)
    return f"Panel updated with {n} section{'s' if n != 1 else ''}." if n else "Panel cleared."


@mcp.tool()
async def panel_script(code: str, title: str = "Animation") -> str:
    """Run a Python script in the panel viewer for animated/dynamic content.

    The script executes inside the Textual viewer and receives:
      - canvas: a RichLog widget — call canvas.write(...) to display content
      - sleep: an async sleep function for timing animations
      - width: int — available width in characters (fills the panel)
      - height: int — available height in lines (fills the panel)
      - Rich library classes: Text, Panel, Table, Columns, Syntax, etc.

    Example:
      panel_script(
        code="for i in range(5):\\n    canvas.write(f'Step {i+1}')\\n    await sleep(0.5)",
        title="Demo"
      )
    """
    _write_state({"mode": "script", "script": {"code": code, "title": title}})
    return f"Script '{title}' sent to panel viewer."


@mcp.tool()
async def screensaver_save(name: str, code: str) -> str:
    """Save a screensaver animation script.

    The code should represent one cycle of the animation. The viewer will
    loop it continuously until interrupted by panel() or panel_script().

    The script receives the same namespace as panel_script:
      canvas, sleep, width, height, Text, Panel, Table, etc.

    Write the code as a single pass — the viewer wraps it in a loop.

    Example:
      screensaver_save(
        name="matrix",
        code="import random\\nfor _ in range(height):\\n    line = ''.join(random.choice(' .o0') for _ in range(width))\\n    canvas.write(Text(line, style='green'))\\nawait sleep(0.1)\\ncanvas.clear()"
      )
    """
    SCREENSAVERS_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSAVERS_DIR / f"{name}.py"
    path.write_text(code)
    return f"Screensaver '{name}' saved."


@mcp.tool()
async def screensaver_play(name: str) -> str:
    """Play a saved screensaver by name. Loops until interrupted.

    Use screensaver_list() to see available screensavers.
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
