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
You are a status dashboard curator. You update a structured dashboard panel \
that shows: current task, files changed, and decisions made.

You ONLY update the status screen — never touch the main screen.

## Current status content

{current_status}

## Recent conversation

{transcript}

## Your task

Extract from the conversation:
1. **task** — What is the current task/goal? One line.
2. **files** — What files have been changed or discussed? Bullet list with one-line descriptions.
3. **decisions** — What non-obvious decisions were made and why? Bullet list.

Return ONLY valid JSON, no markdown fences:

{{"task": "...", "files": "- file.py — what changed", "decisions": "- decision — why"}}

- Set a field to null if it hasn't changed from the current status.
- Keep each field short and scannable.
- If nothing meaningful changed, return {{"task": null, "files": null, "decisions": null}}
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
    logger.info(f"Hook input keys: {list(hook_input.keys())}")
    last_msg = hook_input.get("last_assistant_message", {})
    logger.info(f"Transcript path: {transcript_path!r}")
    logger.info(f"last_assistant_message keys: {list(last_msg.keys()) if isinstance(last_msg, dict) else type(last_msg).__name__}")
    logger.info(f"last_assistant_message sample: {json.dumps(last_msg)[:500]}")
    if not transcript_path:
        logger.info("No transcript path, skipping")
        return

    transcript = read_transcript_tail(transcript_path)
    if not transcript:
        return

    state = read_state()
    current_status = format_current_status(state)

    prompt = STATUS_PROMPT.format(
        current_status=current_status,
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

        # Apply status updates (skip nulls)
        changed = False
        for field in ("task", "files", "decisions"):
            value = updates.get(field)
            if value is not None:
                state = update_status_section(state, field, value)
                changed = True

        if changed:
            write_state(state)
            logger.info("Status screen updated")
        else:
            logger.info("No status changes needed")

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
