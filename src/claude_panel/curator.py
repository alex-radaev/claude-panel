"""Panel curator — background agent that silently manages panel content.

Runs as a UserPromptSubmit hook. Reads the conversation transcript,
decides what the panel should show, and writes directly to state.json.
Zero noise in the main conversation.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from claude_panel.constants import (
    CONFIG_FILE,
    CURATOR_LOG,
    PANEL_DIR,
    SCREENSAVERS_DIR,
    STATE_FILE,
)

# ── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    filename=str(CURATOR_LOG),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("curator")

# ── Standard screen ordering ────────────────────────────────────────

STANDARD_ORDER = ["main", "status", "ambient"]

DEFAULT_CONFIG = {
    "model": "claude-sonnet-4-6",
    "favorite_screensaver": "tokyo-drift",
    "update_every_n": 1,
}

STATUS_SECTIONS = [
    {"id": "task", "title": "Current Task", "content": "*Not set*"},
    {"id": "files", "title": "Files Changed", "content": "*None yet*"},
    {"id": "decisions", "title": "Decisions", "content": "*None yet*"},
]

# ── Curator prompt ──────────────────────────────────────────────────

CURATOR_PROMPT = """\
You are a panel curator for a developer's side panel. The panel is a persistent \
TUI display next to their Claude Code conversation. Your job is to decide what \
the panel should show RIGHT NOW to be most useful to the developer.

## The panel has 3 screens

1. **main** — Free-form canvas. Show whatever is most relevant: plans, progress, \
explanations, diagrams, key context. You have full creative control.
2. **status** — Structured dashboard with fixed sections: task, files, decisions.
3. **ambient** — Screensaver (you don't manage this, just choose when to show it).

## Current panel state

{current_state}

## Recent conversation

{transcript}

## Latest user message

{user_prompt}

## Your task

Based on the conversation and what the user just said, decide:
1. Does the panel need updating? (If the user is just chatting, maybe not.)
2. What should the **main** screen show? Think about what context is most useful \
RIGHT NOW — not a summary of what happened, but what the developer needs to see \
while reading Claude's response.
3. What should the **status** sections say?
   - **task**: What is the current task/goal?
   - **files**: What files have been changed or are being discussed?
   - **decisions**: What non-obvious decisions have been made and why?
4. Which screen should be **active**? Show main when there's useful context, \
ambient when idle or casual chat.
5. Should the **screensaver** change? If the user asks to switch the screensaver \
(e.g., "switch to matrix", "rainy vibes", "show me space-flight"), set the \
`ambient` field. Available screensavers: {available_screensavers}

## Response format

Return ONLY valid JSON, no markdown fences:

{{
  "update": true,
  "active": "main",
  "main": {{
    "sections": [
      {{"id": "section-id", "title": "Section Title", "content": "Markdown content..."}}
    ]
  }},
  "status": {{
    "task": "Current task description or null to keep unchanged",
    "files": "File list or null to keep unchanged",
    "decisions": "Decisions list or null to keep unchanged"
  }},
  "ambient": "screensaver-name or null to keep unchanged"
}}

- Set `"update": false` if nothing meaningful changed — do not update just to update.
- Omit `main` entirely if the main screen doesn't need to change.
- Set individual status fields to `null` to keep them unchanged.
- Set `ambient` to a screensaver name to switch it, or `null` to keep current.
- `active` can be "main", "status", or "ambient".
- Section IDs must be lowercase with hyphens only (no apostrophes, spaces, etc.).
- Keep content short and scannable — the developer glances at this, not reads essays.
- Use markdown: headers, bullet lists, checkboxes `- [x]`, code blocks, **bold**.
"""

# ── Config ──────────────────────────────────────────────────────────


def read_config() -> dict[str, Any]:
    """Read curator config, falling back to defaults."""
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            user_config = json.loads(CONFIG_FILE.read_text())
            config.update(user_config)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read config: {e}")
    return config


# ── Transcript ──────────────────────────────────────────────────────


def read_transcript_tail(path: str, max_bytes: int = 50_000) -> str:
    """Read the last ~max_bytes of the transcript file."""
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
                # Skip partial first line
                f.readline()
            raw = f.read().decode("utf-8", errors="replace")
        return raw
    except OSError as e:
        logger.warning(f"Failed to read transcript: {e}")
        return ""


# ── Panel state ─────────────────────────────────────────────────────


def read_current_state() -> dict[str, Any]:
    """Read the current panel state."""
    if not STATE_FILE.exists():
        return {}
    try:
        raw = STATE_FILE.read_text()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def format_current_state(state: dict[str, Any]) -> str:
    """Format current panel state for the curator prompt."""
    if not state or state.get("mode") != "multi":
        return "(Panel is empty — no screens set up yet.)"

    parts = []
    screens = state.get("screens", {})
    active = state.get("active", "none")
    parts.append(f"Active screen: {active}")

    for name in state.get("screen_order", []):
        screen = screens.get(name, {})
        stype = screen.get("type", "unknown")
        if stype == "screensaver":
            parts.append(f"\n**{name}** (screensaver: {screen.get('name', '?')})")
        elif stype in ("sections", "file"):
            sections = screen.get("sections", [])
            parts.append(f"\n**{name}** ({len(sections)} sections):")
            for s in sections:
                content_preview = s.get("content", "")[:200]
                parts.append(f"  - [{s.get('id')}] {s.get('title')}: {content_preview}")

    return "\n".join(parts)


def write_state_atomic(state: dict[str, Any]) -> None:
    """Atomically write state to the shared JSON file."""
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
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


def _ensure_screen_order(order: list[str]) -> list[str]:
    """Standard screens first, custom screens after."""
    standard = [s for s in STANDARD_ORDER if s in order]
    custom = [s for s in order if s not in STANDARD_ORDER]
    return standard + custom


# ── LLM call ────────────────────────────────────────────────────────


async def call_curator(
    transcript: str,
    current_state_str: str,
    user_prompt: str,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    """Call the configured model with the curator prompt."""
    # List available screensavers
    available = []
    if SCREENSAVERS_DIR.exists():
        available = sorted(p.stem for p in SCREENSAVERS_DIR.glob("*.py"))

    prompt = CURATOR_PROMPT.format(
        current_state=current_state_str,
        transcript=transcript,
        user_prompt=user_prompt,
        available_screensavers=", ".join(available) if available else "none",
    )

    model = config.get("model", DEFAULT_CONFIG["model"])
    logger.info(f"Calling {model} for panel curation")

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
            logger.warning("LLM returned empty response")
            return None

        # Strip markdown code fences if present
        text = result_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}\nResponse: {result_text[:500]}")
        return None
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None


# ── Apply updates ───────────────────────────────────────────────────


def apply_updates(updates: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Merge curator updates into current panel state."""
    if state.get("mode") != "multi":
        state = {"mode": "multi", "screens": {}, "screen_order": [], "active": None}

    screens = state.get("screens", {})
    order = list(state.get("screen_order", []))

    # Update main screen
    if "main" in updates and updates["main"]:
        main_data = updates["main"]
        sections = main_data.get("sections", [])
        if sections:
            screens["main"] = {"type": "sections", "sections": sections}
            if "main" not in order:
                order.append("main")

    # Update status screen (incremental)
    if "status" in updates and updates["status"]:
        status_update = updates["status"]
        # Get or initialize status screen
        status_screen = screens.get("status")
        if status_screen is None or status_screen.get("type") != "sections":
            status_screen = {"type": "sections", "sections": [dict(s) for s in STATUS_SECTIONS]}

        existing = status_screen.get("sections", [])
        for field in ("task", "files", "decisions"):
            value = status_update.get(field)
            if value is None:
                continue  # null = keep unchanged
            # Find and update section
            found = False
            for s in existing:
                if s.get("id") == field:
                    s["content"] = value
                    found = True
                    break
            if not found:
                title = field.replace("_", " ").replace("-", " ").title()
                existing.append({"id": field, "title": title, "content": value})

        status_screen["sections"] = existing
        screens["status"] = status_screen
        if "status" not in order:
            order.append("status")

    # Update ambient screensaver if requested
    ambient_name = updates.get("ambient")
    if ambient_name and isinstance(ambient_name, str):
        saver_path = SCREENSAVERS_DIR / f"{ambient_name}.py"
        if saver_path.exists():
            code = saver_path.read_text()
            screens["ambient"] = {"type": "screensaver", "name": ambient_name, "code": code}
            if "ambient" not in order:
                order.append("ambient")
            logger.info(f"Switched screensaver to '{ambient_name}'")

    # Set active screen
    active = updates.get("active")
    if active and active in screens:
        state["active"] = active
    elif active == "ambient" and "ambient" in screens:
        state["active"] = "ambient"

    state["screens"] = screens
    state["screen_order"] = _ensure_screen_order(order)
    return state


# ── Throttle ────────────────────────────────────────────────────────

NUDGE_FILE = PANEL_DIR / ".nudge_state"


def should_run(config: dict[str, Any]) -> bool:
    """Check if we should run this turn (throttling)."""
    every_n = config.get("update_every_n", 1)
    if every_n <= 1:
        return True

    count = 0
    if NUDGE_FILE.exists():
        try:
            count = int(NUDGE_FILE.read_text().strip())
        except (ValueError, OSError):
            count = 0

    count += 1
    try:
        NUDGE_FILE.write_text(str(count))
    except OSError:
        pass

    return count % every_n == 0


# ── Main ────────────────────────────────────────────────────────────


async def run(hook_input: dict[str, Any]) -> None:
    """Main curator flow."""
    config = read_config()

    if not should_run(config):
        logger.info("Skipping (throttled)")
        return

    transcript_path = hook_input.get("transcript_path", "")
    user_prompt = hook_input.get("user_prompt", "")

    if not transcript_path and not user_prompt:
        logger.info("No transcript or prompt, skipping")
        return

    # Read inputs
    transcript = read_transcript_tail(transcript_path)
    state = read_current_state()
    state_str = format_current_state(state)

    # Call LLM
    updates = await call_curator(transcript, state_str, user_prompt, config)
    if updates is None:
        logger.info("No updates from curator")
        return

    if not updates.get("update", False):
        logger.info("Curator decided no update needed")
        return

    # Apply and write
    new_state = apply_updates(updates, state)
    write_state_atomic(new_state)
    logger.info(f"Panel updated. Active: {new_state.get('active')}")


def main():
    """Entry point for hook script."""
    try:
        raw = sys.stdin.read()
        hook_input = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    import asyncio
    asyncio.run(run(hook_input))


if __name__ == "__main__":
    main()
