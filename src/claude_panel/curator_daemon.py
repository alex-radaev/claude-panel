"""Persistent curator daemon — holds a warm ClaudeSDKClient for fast updates.

Launched on session start, polls for nudge signals from the stop hook.
The persistent client maintains conversation context across calls,
so the curator naturally remembers what it showed before.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

from claude_panel.constants import (
    CONFIG_FILE,
    DEFAULT_SCREENSAVER,
    PANEL_DIR,
    resolve_screensaver,
)
from claude_panel.curator import (
    build_prompt,
    ensure_ambient,
    ensure_multi,
    ensure_screen_order,
    format_current_status,
    read_config,
    read_state,
    read_transcript_tail,
    update_main,
    update_mood,
    update_status_section,
    write_state,
    STATUS_SECTIONS,
)
from claude_panel.session import session_state_file

logger = logging.getLogger("curator-daemon")

POLL_INTERVAL = 0.5  # seconds between nudge checks


def _nudge_file(session_id: str) -> Path:
    """Path to the nudge signal file for this session."""
    return session_state_file(session_id).parent / "curator_nudge.json"


def _pid_file(session_id: str) -> Path:
    """Path to the daemon PID file for this session."""
    return session_state_file(session_id).parent / "curator_daemon.pid"


def _read_nudge(session_id: str) -> dict[str, Any] | None:
    """Read and consume the nudge signal."""
    path = _nudge_file(session_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        path.unlink()  # consume it
        return data
    except (json.JSONDecodeError, OSError):
        try:
            path.unlink()
        except OSError:
            pass
        return None


async def run_daemon(session_id: str) -> None:
    """Main daemon loop — warm up client, poll for nudges, update panel."""
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

    config = read_config()
    model = config.get("model", "claude-haiku-4-5-20251001")
    personality = config.get("curator_personality", "playful")

    # Write PID file
    pid_file = _pid_file(session_id)
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))

    logger.info(f"Curator daemon started: session={session_id} model={model} personality={personality}")

    # System prompt for the persistent conversation
    system_prompt = _build_system_prompt(config)

    options = ClaudeAgentOptions(
        model=model,
        max_turns=1,
        output_format="json",
        system_prompt=system_prompt,
    )
    client = ClaudeSDKClient(options)

    # Warm up the client with an initial connect
    warmup_prompt = (
        "You are now active as the panel curator. "
        "Respond with: {\"status\": \"ready\"}"
    )
    try:
        logger.info("Warming up client...")
        start = time.time()
        await client.connect(warmup_prompt)
        async for message in client.receive_messages():
            if hasattr(message, "result") and message.result:
                break
        elapsed = time.time() - start
        logger.info(f"Client warm in {elapsed:.1f}s")
    except Exception as e:
        logger.error(f"Failed to warm up client: {e}")
        await client.disconnect()
        return

    # Main poll loop
    try:
        while True:
            await asyncio.sleep(POLL_INTERVAL)

            nudge = _read_nudge(session_id)
            if nudge is None:
                continue

            transcript_path = nudge.get("transcript_path", "")
            if not transcript_path:
                continue

            try:
                await _handle_update(client, session_id, transcript_path, config)
            except Exception as e:
                logger.error(f"Update failed: {e}")

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Daemon shutting down")
    finally:
        await client.disconnect()
        try:
            pid_file.unlink()
        except OSError:
            pass
        logger.info("Daemon stopped")


async def _handle_update(
    client: Any, session_id: str, transcript_path: str, config: dict[str, Any]
) -> None:
    """Process one nudge — read state, query the warm client, update panel."""
    start = time.time()

    transcript = read_transcript_tail(transcript_path)
    if not transcript:
        return

    state = read_state(session_id)
    state = ensure_ambient(state)
    current_status = format_current_status(state)

    # Get current mood
    main_screen = state.get("screens", {}).get("main", {})
    current_mood = (
        f"{main_screen.get('emoji', '?')} — {main_screen.get('context', 'not set')}"
        if main_screen.get("emoji")
        else "Not set"
    )

    # Build the update prompt (no history needed — client has its own context)
    from datetime import datetime
    prompt = (
        f"**Current time:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"## Current panel state\n\n"
        f"**Status:** {current_status}\n\n"
        f"**Main screen:** {current_mood}\n\n"
        f"## Recent conversation\n\n{transcript}\n\n"
        "Update the panel now. Return ONLY a JSON object."
    )

    # Query the warm client
    result_text = ""
    try:
        client.query(prompt)
        async for message in client.receive_messages():
            if message is None:
                continue
            if hasattr(message, "result") and message.result:
                result_text = message.result
                break
            elif hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        result_text += block.text
    except Exception as e:
        logger.error(f"Client query failed: {e}")
        return

    elapsed_llm = time.time() - start

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

    try:
        updates = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse response: {e}\n{text[:300]}")
        return

    # Apply updates
    changed = False
    for field in ("task", "files", "decisions"):
        value = updates.get(field)
        if value is not None:
            if isinstance(value, list):
                value = "\n".join(f"- {v}" if not v.startswith("-") else v for v in value)
            state = update_status_section(state, field, str(value))
            changed = True

    main_mode = updates.get("main_mode", "mood")
    emoji = updates.get("emoji", "")

    if main_mode == "sections":
        main_sections = updates.get("main_sections", [])
        if main_sections:
            if emoji and main_sections[0].get("title"):
                main_sections[0]["title"] = f"{emoji} {main_sections[0]['title']}"
            state = update_main(state, main_sections)
            changed = True
            logger.info(f"Main: {emoji} rich content ({len(main_sections)} sections) [{elapsed_llm:.1f}s]")
    else:
        context = updates.get("context", "")
        if emoji and context:
            state = update_mood(state, emoji, context)
            changed = True
            logger.info(f"Mood: {emoji} {context} [{elapsed_llm:.1f}s]")

    if changed:
        write_state(state, session_id)
        logger.info(f"Panel updated [{elapsed_llm:.1f}s total]")
    else:
        logger.info("No changes needed")


def _build_system_prompt(config: dict[str, Any]) -> str:
    """Build the persistent system prompt for the curator."""
    from claude_panel.curator import PERSONALITIES, PERSONALITY_PLAYFUL

    personality_name = config.get("curator_personality", "playful")
    personality = PERSONALITIES.get(personality_name, PERSONALITY_PLAYFUL)

    return f"""\
You are a panel curator — you manage a developer's side panel next to their Claude Code terminal.
{personality['intro']}

You will receive periodic updates with the current panel state and recent conversation.
Update the panel based on what changed.

{personality['guidelines']}

## Response format

Return ONLY a single JSON object. No text before or after. No markdown fences. Just raw JSON.

Rich content:
{{"task": "...", "files": "...", "decisions": "...", "emoji": "🔥", "main_mode": "sections", "main_sections": [{{"id": "what-changed", "title": "What Changed", "content": "..."}}]}}

Mood emoji:
{{"task": "...", "files": "...", "decisions": "...", "emoji": "☕", "main_mode": "mood", "context": "..."}}

Rules:
- Always include emoji
- Set status fields to null if unchanged
- Keep content short and scannable
- Use markdown: bold, code, bullet lists, checkboxes
- Rich sections: 1-3 max
{personality['closing']}
"""


def write_nudge(session_id: str, transcript_path: str) -> None:
    """Write a nudge signal for the daemon (called from the stop hook)."""
    path = _nudge_file(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"transcript_path": transcript_path, "ts": time.time()}
    path.write_text(json.dumps(data))


def is_daemon_running(session_id: str) -> bool:
    """Check if the daemon is running for this session."""
    path = _pid_file(session_id)
    if not path.exists():
        return False
    try:
        pid = int(path.read_text().strip())
        os.kill(pid, 0)  # check if process exists
        return True
    except (ValueError, OSError):
        try:
            path.unlink()
        except OSError:
            pass
        return False


def main():
    """Entry point — start the daemon for a session."""
    if len(sys.argv) < 2:
        print("Usage: curator_daemon <session_id>", file=sys.stderr)
        sys.exit(1)

    session_id = sys.argv[1]

    # Set up logging
    log_file = PANEL_DIR / "curator.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    # Handle graceful shutdown
    def handle_signal(signum, frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, handle_signal)

    asyncio.run(run_daemon(session_id))


if __name__ == "__main__":
    main()
