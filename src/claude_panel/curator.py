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


EMOJI_DIR = PANEL_DIR / "emoji"

EMOJI_MAP = {
    "🔥": "fire", "🤔": "thinking", "🎯": "target", "🎉": "celebration",
    "🏗️": "building", "🐛": "bug", "💡": "lightbulb", "☕": "coffee",
    "⚡": "urgent", "🧪": "testing", "🎨": "designing", "📚": "learning",
    "🚀": "rocket", "🔧": "refactoring",
}


def update_mood(state: dict[str, Any], emoji: str, context: str, tip: str = "") -> dict[str, Any]:
    """Update main screen with a big Rich-styled emoji + context + optional tip.

    Loads a Python script from ~/.claude-panel/emoji/<name>.py if available.
    The script receives CONTEXT and TIP variables plus the standard canvas/Rich namespace.
    Falls back to a simple centered display.
    """
    art_name = EMOJI_MAP.get(emoji, "")
    script_path = EMOJI_DIR / f"{art_name}.py" if art_name else None

    if script_path and script_path.exists():
        code = script_path.read_text()
    else:
        # Fallback: simple centered emoji
        code = f"""
from rich.text import Text
from rich.align import Align
canvas.write(Text(""))
canvas.write(Text(""))
canvas.write(Align.center(Text("{emoji}", style="bold")))
canvas.write(Text(""))
canvas.write(Align.center(Text("━" * 40, style="dim")))
canvas.write(Text(""))
canvas.write(Align.center(Text(CONTEXT, style="bold")))
if TIP:
    canvas.write(Text(""))
    canvas.write(Align.center(Text(TIP, style="dim italic")))
"""

    # Inject CONTEXT and TIP as variables into the script
    header = f'CONTEXT = {context!r}\nTIP = {tip!r}\n'
    full_code = header + code

    state = ensure_multi(state)
    screens = state.get("screens", {})
    order = list(state.get("screen_order", []))
    screens["main"] = {"type": "mood", "code": full_code, "emoji": emoji, "context": context}
    if "main" not in order:
        order.append("main")
    state["screens"] = screens
    state["screen_order"] = ensure_screen_order(order)
    state["active"] = "main"
    return state


# ── Hook-based status curator ──────────────────────────────────────
# Runs as a Stop hook. Only updates the status screen (task, files, decisions).
# Main screen is handled by background agents spawned by main Claude.

import logging
import sys
from pathlib import Path

CONFIG_FILE = PANEL_DIR / "config.json"
CURATOR_LOG = PANEL_DIR / "curator.log"

logging.basicConfig(
    filename=str(CURATOR_LOG),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("curator")

DEFAULT_CONFIG = {
    "model": "claude-haiku-4-5-20251001",
    "favorite_screensaver": "tokyo-drift",
    "update_every_n": 1,
}

STATUS_PROMPT = """\
You are a panel curator managing a developer's side panel. You update:
1. **Status screen** — task, files changed, decisions (structured dashboard)
2. **Main screen** — YOUR creative canvas. Show whatever is most useful right now.

## Current panel state

**Status:** {current_status}

**Main screen:** {current_mood}

## Recent conversation

{transcript}

## Your task

### Status (structured — always update)
1. **task** — Current task/goal. One line.
2. **files** — Files changed or discussed. Bullet list with descriptions.
3. **decisions** — Non-obvious decisions made. Bullet list with why.

### Main screen (creative — you decide what to show)

Choose the BEST format for what's happening right now:

**Option A: Mood emoji** — for simple states (idle, focused, celebrating)
Return `"main_mode": "mood"` with `"emoji"` and `"context"`.

**Option B: Rich content** — for complex work (explanations, diagrams, concepts)
Return `"main_mode": "sections"` with `"main_sections"` array.

Use rich content when:
- Claude is explaining something complex → show the key concept/diagram
- Multi-step work → show a progress checklist
- Architecture discussion → show a diagram
- Debugging → show hypothesis and evidence
- Claude's internal thinking would help the user understand what's happening

Use mood emoji when:
- Idle / casual chat → ☕
- Simple progress, no complex context → 🔥 🎯 🏗️
- Just completed something → 🎉
- Nothing specific to visualize

### Emoji vocabulary (for mood mode):
🔥 on fire  🤔 thinking  🎯 focused  🎉 done  🏗️ building  🐛 debugging
💡 insight  ☕ chill  ⚡ urgent  🧪 testing  🎨 designing  📚 learning
🚀 shipping  🔧 refactoring

## Response format

Return ONLY valid JSON, no markdown fences:

For mood:
{{"task": "...", "files": "...", "decisions": "...", "main_mode": "mood", "emoji": "🔥", "context": "Making fast progress"}}

For rich content:
{{"task": "...", "files": "...", "decisions": "...", "main_mode": "sections", "main_sections": [{{"id": "concept", "title": "Key Concept", "content": "markdown..."}}, {{"id": "progress", "title": "Progress", "content": "- [x] step 1..."}}]}}

- Set status fields to null if unchanged.
- Keep main content short and scannable — the user glances at the panel.
- Use markdown in content: **bold**, `code`, bullet lists, checkboxes.
"""


def read_config() -> dict[str, Any]:
    """Read curator config."""
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            config.update(json.loads(CONFIG_FILE.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    return config


def read_transcript_tail(path: str, max_bytes: int = 30_000) -> str:
    """Read the last ~max_bytes of the transcript."""
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    try:
        size = p.stat().st_size
        with open(p, "rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                f.readline()  # skip partial line
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def format_current_status(state: dict[str, Any]) -> str:
    """Format current status screen for the prompt."""
    screens = state.get("screens", {})
    status = screens.get("status", {})
    if status.get("type") != "sections":
        return "(Status screen not initialized)"
    parts = []
    for s in status.get("sections", []):
        parts.append(f"**{s.get('id')}**: {s.get('content', '')[:200]}")
    return "\n".join(parts)


async def run_status_curator(hook_input: dict[str, Any]) -> None:
    """Main entry point for the Stop hook — updates status screen only."""
    config = read_config()

    # Throttle
    every_n = config.get("update_every_n", 1)
    nudge_file = PANEL_DIR / ".nudge_state"
    if every_n > 1:
        count = 0
        if nudge_file.exists():
            try:
                count = int(nudge_file.read_text().strip())
            except (ValueError, OSError):
                count = 0
        count += 1
        try:
            nudge_file.write_text(str(count))
        except OSError:
            pass
        if count % every_n != 0:
            return

    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path:
        logger.info("No transcript path, skipping")
        return

    transcript = read_transcript_tail(transcript_path)
    if not transcript:
        return

    state = read_state()
    current_status = format_current_status(state)

    # Get current mood
    main_screen = state.get("screens", {}).get("main", {})
    current_mood = f"{main_screen.get('emoji', '?')} — {main_screen.get('context', 'not set')}" if main_screen.get("emoji") else "Not set"

    prompt = STATUS_PROMPT.format(
        current_status=current_status,
        current_mood=current_mood,
        transcript=transcript,
    )

    model = config.get("model", DEFAULT_CONFIG["model"])
    logger.info(f"Status curator: calling {model}")

    try:
        from claude_agent_sdk import query as sdk_query, ClaudeAgentOptions

        options = ClaudeAgentOptions(model=model, max_turns=1)
        result_text = ""

        async for message in sdk_query(prompt=prompt, options=options):
            if message is None:
                continue
            if hasattr(message, "result") and message.result:
                result_text = message.result
            elif hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        result_text += block.text

        if not result_text:
            logger.warning("Empty response from LLM")
            return

        # Parse JSON
        text = result_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        updates = json.loads(text)

        # Apply status updates (skip nulls, ensure strings)
        changed = False
        for field in ("task", "files", "decisions"):
            value = updates.get(field)
            if value is not None:
                # LLM sometimes returns lists instead of strings
                if isinstance(value, list):
                    value = "\n".join(f"- {v}" if not v.startswith("-") else v for v in value)
                state = update_status_section(state, field, str(value))
                changed = True

        # Apply main screen update — curator decides mood vs rich content
        main_mode = updates.get("main_mode", "mood")

        if main_mode == "sections":
            # Rich content — curator wants to show explanations/diagrams/progress
            main_sections = updates.get("main_sections", [])
            if main_sections:
                state = update_main(state, main_sections)
                changed = True
                logger.info(f"Main: rich content ({len(main_sections)} sections)")
        else:
            # Mood emoji
            emoji = updates.get("emoji")
            context = updates.get("context", "")
            if emoji and context:
                state = update_mood(state, emoji, context)
                changed = True
                logger.info(f"Mood: {emoji} {context}")

        if changed:
            write_state(state)
            logger.info("Panel updated (status + mood)")
        else:
            logger.info("No changes needed")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse response: {e}\n{result_text[:300]}")
    except Exception as e:
        logger.error(f"Status curator failed: {e}")


def main():
    """Entry point for hook script."""
    try:
        raw = sys.stdin.read()
        hook_input = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    import asyncio
    asyncio.run(run_status_curator(hook_input))


if __name__ == "__main__":
    main()
