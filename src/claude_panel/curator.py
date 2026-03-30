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
    CONFIG_FILE,
    DEFAULT_SCREENSAVER,
    PANEL_DIR,
    STATE_FILE,
    resolve_screensaver,
)
from claude_panel.session import (
    get_session_id_from_transcript,
    session_state_file,
    set_active_session,
)

STANDARD_ORDER = ["main", "status", "ambient"]

STATUS_SECTIONS = [
    {"id": "objective", "title": "Objective", "content": "*Not set*"},
    {"id": "decisions", "title": "Decisions", "content": "*None yet*"},
    {"id": "constraints", "title": "Constraints", "content": "*None yet*"},
    {"id": "open_questions", "title": "Open Questions", "content": "*None yet*"},
]


def _resolve_state_file(session_id: str | None) -> tuple[Path, Path]:
    """Return (state_file, parent_dir) for a session or the global fallback."""
    if session_id:
        sf = session_state_file(session_id)
        return sf, sf.parent
    return STATE_FILE, PANEL_DIR


def read_state(session_id: str | None = None) -> dict[str, Any]:
    """Read current panel state for a session (or global fallback)."""
    state_file, _ = _resolve_state_file(session_id)
    if not state_file.exists():
        return {}
    try:
        raw = state_file.read_text()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _log_panel_state(state: dict[str, Any], parent_dir: Path) -> None:
    """Append a snapshot of the full panel state to history log."""
    try:
        screens = state.get("screens", {})
        if not screens:
            return

        entry: dict[str, Any] = {"ts": time.time()}

        # Main screen
        main = screens.get("main", {})
        stype = main.get("type", "")
        if stype == "mood":
            entry["main"] = f"{main.get('emoji', '')} {main.get('context', '')}"
        elif stype == "sections":
            titles = [s.get("title", "") for s in main.get("sections", [])[:3]]
            entry["main"] = " | ".join(titles)

        # Status screen
        status = screens.get("status", {})
        if status.get("type") == "sections":
            for s in status.get("sections", []):
                if s.get("id") == "objective":
                    entry["objective"] = s.get("content", "")[:100]
                    break

        # Ambient screen
        ambient = screens.get("ambient", {})
        if ambient.get("type") == "screensaver":
            entry["ambient"] = ambient.get("name", "?")

        history_file = parent_dir / "curator_history.jsonl"
        lines = []
        if history_file.exists():
            lines = history_file.read_text().strip().splitlines()
        lines.append(json.dumps(entry))
        if len(lines) > MAX_HISTORY_ENTRIES * 3:
            lines = lines[-MAX_HISTORY_ENTRIES:]
        history_file.write_text("\n".join(lines) + "\n")
    except Exception:
        pass  # never break state writes for logging


def write_state(state: dict[str, Any], session_id: str | None = None) -> None:
    """Atomically write state, clearing loading flag.

    When session_id is provided, writes to the per-session state file
    and marks this session as active. Also logs main screen changes to
    curator_history.jsonl for continuity.
    """
    state_file, parent_dir = _resolve_state_file(session_id)
    parent_dir.mkdir(parents=True, exist_ok=True)
    state.pop("loading", None)
    state.pop("loading_message", None)
    state["ts"] = time.time()

    # Log main screen content for curator continuity
    _log_panel_state(state, parent_dir)

    fd, tmp_path = tempfile.mkstemp(dir=str(parent_dir), suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(state, f)
        os.rename(tmp_path, str(state_file))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    if session_id:
        set_active_session(session_id)


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


def ensure_ambient(state: dict[str, Any]) -> dict[str, Any]:
    """Ensure the ambient screen has a screensaver loaded."""
    state = ensure_multi(state)
    screens = state.get("screens", {})
    if "ambient" in screens:
        return state

    # Pick screensaver: config favorite -> default -> first available
    name = DEFAULT_SCREENSAVER
    try:
        if CONFIG_FILE.exists():
            cfg = json.loads(CONFIG_FILE.read_text())
            name = cfg.get("favorite_screensaver", name)
    except Exception:
        pass

    path = resolve_screensaver(name)
    if not path:
        return state

    screens["ambient"] = {"type": "screensaver", "name": name, "code": path.read_text()}
    order = list(state.get("screen_order", []))
    if "ambient" not in order:
        order.append("ambient")
    state["screens"] = screens
    state["screen_order"] = ensure_screen_order(order)
    return state


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
    "curator_personality": "playful",
}

MAX_HISTORY_ENTRIES = 4

STATUS_PROMPT_BASE = """\
You curate a developer's side panel — a persistent display next to their Claude Code conversation. \
{personality_intro}

**Current time:** {current_time}

## Current panel state

**Status:** {current_status}

**Main screen:** {current_mood}

{history_section}

## Recent conversation

{transcript}

## Screen roles

**STATUS = durable memory.** Information that remains useful across many turns, after a break, \
or tomorrow morning. Calm, sticky, reliable. Not a live progress feed.

**MAIN = active working surface.** Fluid, dynamic, updates often. Shows the most useful current \
representation for the human right now. Reduces cognitive load during active work.

STATUS and MAIN complement each other: STATUS stores durable conclusions, MAIN explores and \
elaborates current details. Avoid blind duplication — MAIN may expand a STATUS item into a \
snippet, flow, or plan.

## What to update

### Status screen (durable memory — always update)

Use this test: *"Would this still be worth showing 20 messages later, after a break, or tomorrow morning?"*

- **objective** — Stable goal, milestone, or workstream. Higher-level than a short task. \
Should not change every few messages unless the workstream truly changes. \
Good: "make tenant-aware session validation correct". Bad: "inspect helper", "rerun tests".
- **decisions** — Durable choices already made. Concise and factual. \
Example: "use tenant-agnostic session validation", "tenant is encoded in cookie name".
- **constraints** — Assumptions, invariants, limitations, boundaries the implementation must respect. \
Example: "Firebase tenant-aware session cookies are not available", "cookie tenant must match JWT claim".
- **open_questions** — Unresolved design issues, risks, or uncertainties worth keeping visible. \
Example: "should logout clear one tenant cookie or all?", "do production SameSite rules differ from dev?"

Do NOT put transient activity (recent file edits, momentary debug details) in STATUS. \
Files may appear only occasionally as long-lived key surfaces in semantic form \
(e.g. "auth.py — validation logic").

{personality_status_note}

### Main screen (active working surface)

MAIN should update frequently. Do NOT throttle it. Do NOT make it mostly static.

**Before writing MAIN, choose the most useful content type for the current moment:**

| Content type | When to use |
|--------------|-------------|
| focus_snippet | A code snippet, pseudocode, schema, or contract is central right now |
| immediate_plan | Short near-term plan, 3–5 bullets, active attack plan |
| files_in_play | Files currently central to the work — include *why* they matter |
| recent_changes | Concise human summary of what changed (not a raw diff) |
| blocker | Current unresolved issue, hypothesis, edge case, failure mode |
| flow_or_schema | Architecture flow, data flow, logic flow, decision tree |
| handoff | "What changed / where we are / what's next" state summary |
| mood | Playful filler, vibe, celebration — valid when no concrete working content exists |

**Selection priority:**
- If there is concrete coding substance → prefer focus_snippet / blocker / immediate_plan / recent_changes / flow_or_schema over mood
- If the turn is mostly coordination → prefer handoff / immediate_plan / recent_changes over mood
- If the turn is light, idle, or has little concrete signal → mood is fine

**Preserve useful content:** Do not replace an already-useful MAIN screen with a weaker one \
just because there is a fresh opportunity to update. Only replace useful content with content \
that is at least as useful or more useful.

**Emoji vocabulary (for mood and section titles):**

| Emoji | When |
|-------|------|
| 🔥 | Fast progress, things clicking |
| 🎯 | Clear goal, executing |
| 🏗️ | Building something new |
| 🎉 | Just completed a milestone |
| ☕ | Idle, casual chat, vibing |
| 🤔 | Investigating, unsure |
| 🐛 | Chasing a bug |
| 💡 | Had an insight |
| 🚀 | Shipping, committing |
| 🧹 | Cleaning up, refactoring |
| 🎪 | Something wild or unexpected happening |
| 🌊 | In flow state, deep work |
| 🍕 | Long session, maybe take a break? |

{personality_guidelines}

**Core principle:** Prefer reducing cognitive load over being entertaining. \
Personality is decoration on top of usefulness, not a replacement for usefulness.

## Response format

CRITICAL: Return ONLY a single JSON object. No text before or after. No explanation. No markdown fences. \
Just the raw JSON. If you write anything other than JSON, the panel breaks.

**Rich content (preferred when there's substance):**
{{"objective": "...", "decisions": "...", "constraints": "...", "open_questions": "...", "emoji": "🔥", "main_mode": "sections", "main_sections": [{{"id": "what-changed", "title": "🔥 What Changed", "content": "`auth.py` — added JWT middleware\\n\\n```python\\nasync def verify_token(token: str):\\n    ...\\n```"}}, {{"id": "next", "title": "Next Steps", "content": "- [ ] Add refresh token logic\\n- [ ] Write tests"}}]}}

**Mood emoji (for ambient/simple states):**
{{"objective": "...", "decisions": "...", "constraints": "...", "open_questions": "...", "emoji": "☕", "main_mode": "mood", "context": "{mood_example}"}}

Rules:
- **Always include emoji** — it appears in the section title (rich) or as the main display (mood).
- Set status fields to null if unchanged.
- Keep content **short and scannable** — user glances, not reads.
- Use markdown: **bold**, `code`, ```code blocks```, bullet lists, checkboxes `- [x]`.
- Section IDs: lowercase, hyphens only.
- Rich sections: 1-3 sections max. Don't overload.
{personality_closing}
"""

PERSONALITY_PLAYFUL = {
    "intro": "You're the DJ of this panel: keep it informative, but also **alive, fun, and surprising**. "
             "The user glances at you between code — reward that glance with something worth seeing. "
             "Playfulness is a layer on top of usefulness, not a substitute for usefulness.",
    "status_note": "STATUS tone: keep it mostly neutral. You may slightly warm section phrasing, "
                   "but decisions, constraints, and risks must stay unambiguous. "
                   "Playful flavor belongs mostly on MAIN, not inside durable STATUS facts.",
    "guidelines": """### Personality guidelines

- **Be useful first, charming second.** Every MAIN update should earn its place with real content. \
Wit is the garnish, not the meal.
- **Read the room.** If the conversation is intense debugging, match the energy with a concrete \
blocker/snippet/plan. If it's casual, mood and playfulness are welcome.
- **Surprise the user sometimes.** Drop a fun comment, a relevant joke, an unexpected emoji combo — \
but only when there isn't better concrete content to show.
- **Use the context/tip line creatively on mood screens:**
  - Instead of "Working on auth" → "Teaching the app to check IDs at the door 🪪"
  - Instead of "Waiting for next task" → "Stretching... ready when you are 🧘"
  - Instead of "Bug fixed" → "Squished it. The bug had it coming 🪲💀"
- **Use emoji combos** in context lines for extra flavor (🔥⚡, 🐛🔍, 🚀✨).
- **If the session has been going a while**, gently suggest a break or acknowledge the grind.
- **If something genuinely cool was accomplished**, celebrate it — don't undersell.
- **Never turn important content into a joke.** Charming, not clownish.""",
    "mood_example": "Stretching... ready when you are 🧘",
    "closing": "- **Have personality.** You're not a log file, you're a co-pilot with a sense of humor. "
               "But useful content always wins over filler.",
}

PERSONALITY_PROFESSIONAL = {
    "intro": "Your goal: **show context that saves the user from scrolling back**. The panel is a second "
             "communication channel that makes coding more efficient.",
    "status_note": "STATUS tone: concise, factual, unambiguous. No commentary.",
    "guidelines": """### Tone guidelines

- **Be concise and clear.** Every word should earn its place.
- **Focus on actionable info.** What changed, what's next, what to watch out for.
- **Match the work.** Technical precision over flair.
- **Use context lines for useful info**, not commentary.""",
    "mood_example": "Waiting for next task",
    "closing": "- **Be precise.** Useful beats clever.",
}

PERSONALITIES = {
    "playful": PERSONALITY_PLAYFUL,
    "professional": PERSONALITY_PROFESSIONAL,
}


def _read_history(session_id: str | None) -> list[dict[str, Any]]:
    """Read recent main screen updates for curator continuity."""
    if session_id:
        history_file = session_state_file(session_id).parent / "curator_history.jsonl"
    else:
        history_file = PANEL_DIR / "curator_history.jsonl"
    if not history_file.exists():
        return []
    try:
        lines = history_file.read_text().strip().splitlines()
        return [json.loads(line) for line in lines[-MAX_HISTORY_ENTRIES:]]
    except (json.JSONDecodeError, OSError):
        return []


def _format_history_section(history: list[dict[str, Any]]) -> str:
    """Format history entries for the prompt."""
    if not history:
        return ""
    from datetime import datetime
    lines = ["## Recent panel states (for continuity)\n",
             "What was shown on the panel recently (by you and by Claude):\n"]
    for entry in history:
        ts = entry.get("ts", 0)
        time_str = datetime.fromtimestamp(ts).strftime("%H:%M") if ts else "?"
        main = entry.get("main", "")
        ambient = entry.get("ambient", "")
        parts = []
        if main:
            parts.append(f"main: {main}")
        objective = entry.get("objective", "")
        if objective:
            parts.append(f"objective: {objective}")
        if ambient:
            parts.append(f"ambient: {ambient}")
        lines.append(f"- [{time_str}] {' · '.join(parts)}")
    lines.append("\nUse this for continuity — don't repeat yourself, build on what came before.\n")
    return "\n".join(lines)


def build_prompt(config: dict[str, Any], current_status: str, current_mood: str,
                 transcript: str, history: list[dict[str, Any]]) -> str:
    """Build the curator prompt with the configured personality and history."""
    from datetime import datetime
    personality_name = config.get("curator_personality", "playful")
    personality = PERSONALITIES.get(personality_name, PERSONALITY_PLAYFUL)

    return STATUS_PROMPT_BASE.format(
        personality_intro=personality["intro"],
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        current_status=current_status,
        current_mood=current_mood,
        history_section=_format_history_section(history),
        transcript=transcript,
        personality_status_note=personality["status_note"],
        personality_guidelines=personality["guidelines"],
        mood_example=personality["mood_example"],
        personality_closing=personality["closing"],
    )


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

    transcript_path = hook_input.get("transcript_path", "")
    session_id = get_session_id_from_transcript(transcript_path)

    # Throttle — per-session nudge counter
    every_n = config.get("update_every_n", 1)
    if session_id:
        nudge_dir = session_state_file(session_id).parent
        nudge_dir.mkdir(parents=True, exist_ok=True)
        nudge_file = nudge_dir / ".nudge_state"
    else:
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

    if not transcript_path:
        logger.info("No transcript path, skipping")
        return

    transcript = read_transcript_tail(transcript_path)
    if not transcript:
        return

    state = read_state(session_id)
    state = ensure_ambient(state)
    current_status = format_current_status(state)

    # Get current mood
    main_screen = state.get("screens", {}).get("main", {})
    current_mood = f"{main_screen.get('emoji', '?')} — {main_screen.get('context', 'not set')}" if main_screen.get("emoji") else "Not set"

    # Read history for continuity
    history = _read_history(session_id)

    prompt = build_prompt(
        config=config,
        current_status=current_status,
        current_mood=current_mood,
        transcript=transcript,
        history=history,
    )

    model = config.get("model", DEFAULT_CONFIG["model"])
    logger.info(f"Status curator: calling {model}")

    try:
        from claude_agent_sdk import query as sdk_query, ClaudeAgentOptions

        options = ClaudeAgentOptions(model=model, max_turns=1, output_format="json")
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
        CANONICAL_STATUS = ("objective", "decisions", "constraints", "open_questions")
        changed = False
        for field in CANONICAL_STATUS:
            value = updates.get(field)
            if value is not None:
                # LLM sometimes returns lists instead of strings
                if isinstance(value, list):
                    value = "\n".join(f"- {v}" if not v.startswith("-") else v for v in value)
                state = update_status_section(state, field, str(value))
                changed = True

        # Drop stale sections and enforce canonical order
        screens = state.get("screens", {})
        status_screen = screens.get("status", {})
        if status_screen.get("type") == "sections":
            by_id = {s.get("id"): s for s in status_screen.get("sections", [])}
            status_screen["sections"] = [
                by_id[sid] for sid in CANONICAL_STATUS if sid in by_id
            ]
            screens["status"] = status_screen
            state["screens"] = screens

        # Apply main screen update — curator decides mood vs rich content
        main_mode = updates.get("main_mode", "mood")
        emoji = updates.get("emoji", "")

        if main_mode == "sections":
            main_sections = updates.get("main_sections", [])
            if main_sections:
                # Inject emoji into first section title if provided
                if emoji and main_sections[0].get("title"):
                    main_sections[0]["title"] = f"{emoji} {main_sections[0]['title']}"
                state = update_main(state, main_sections)
                changed = True
                logger.info(f"Main: {emoji} rich content ({len(main_sections)} sections)")
        else:
            context = updates.get("context", "")
            if emoji and context:
                state = update_mood(state, emoji, context)
                changed = True
                logger.info(f"Mood: {emoji} {context}")

        if changed:
            write_state(state, session_id)
            logger.info(f"Panel updated (status + mood) session={session_id}")
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
