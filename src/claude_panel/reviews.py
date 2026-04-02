"""GitHub review notification helpers for claude-panel."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from claude_panel.constants import CONFIG_FILE, REVIEW_STATE_FILE

REVIEW_SECTION_ID = "review-notifications"
DEFAULT_POLL_INTERVAL = 120


def is_enabled() -> bool:
    """Check if review notifications are enabled in config."""
    try:
        if CONFIG_FILE.exists():
            cfg = json.loads(CONFIG_FILE.read_text())
            rn = cfg.get("review_notifications", {})
            if isinstance(rn, bool):
                return rn
            return rn.get("enabled", True)
    except (json.JSONDecodeError, OSError):
        pass
    return True


def get_poll_interval() -> int:
    """Get poll interval in seconds from config."""
    try:
        if CONFIG_FILE.exists():
            cfg = json.loads(CONFIG_FILE.read_text())
            rn = cfg.get("review_notifications", {})
            if isinstance(rn, dict):
                return int(rn.get("poll_interval_seconds", DEFAULT_POLL_INTERVAL))
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    return DEFAULT_POLL_INTERVAL


def read_review_state() -> dict[str, Any]:
    """Read the shared review poller state."""
    if not REVIEW_STATE_FILE.exists():
        return {}
    try:
        return json.loads(REVIEW_STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _time_ago(iso_str: str) -> str:
    """Convert ISO timestamp to a human-readable 'N ago' string."""
    try:
        created = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - created
        hours = delta.total_seconds() / 3600
        if hours < 1:
            return f"{int(delta.total_seconds() / 60)}m ago"
        if hours < 24:
            return f"{int(hours)}h ago"
        return f"{int(hours / 24)}d ago"
    except Exception:
        return ""


def format_review_section(review_state: dict[str, Any]) -> dict[str, str] | None:
    """Build the review notification section dict, or None if no reviews."""
    prs = review_state.get("prs", [])
    if not prs:
        return None

    lines = []
    for pr in prs:
        title = pr.get("title", "Untitled")
        url = pr.get("url", "")
        repo = pr.get("repository", {}).get("nameWithOwner", "")
        author = pr.get("author", {}).get("login", "?")
        created = pr.get("createdAt", "")
        ago = _time_ago(created)

        line = f"- \U0001f4a1 [{title}]({url})"
        if repo:
            line += f" \u2014 `{repo}`"
        if author:
            line += f" by @{author}"
        if ago:
            line += f" ({ago})"
        lines.append(line)

    return {
        "id": REVIEW_SECTION_ID,
        "title": "\U0001f4a1 Reviews Requested",
        "content": "\n".join(lines),
    }


def inject_review_notifications(state: dict[str, Any]) -> dict[str, Any]:
    """Inject or remove the review notification section from MAIN screen."""
    if not is_enabled():
        return _strip_review_section(state)

    review_state = read_review_state()
    section = format_review_section(review_state)

    if section is None:
        return _strip_review_section(state)

    # Only inject into sections-type MAIN screens
    screens = state.get("screens", {})
    main = screens.get("main", {})
    if main.get("type") != "sections":
        return state

    existing = main.get("sections", [])
    filtered = [s for s in existing if s.get("id") != REVIEW_SECTION_ID]
    main["sections"] = [section] + filtered
    screens["main"] = main
    state["screens"] = screens
    return state


def _strip_review_section(state: dict[str, Any]) -> dict[str, Any]:
    """Remove the review notification section if present."""
    screens = state.get("screens", {})
    main = screens.get("main", {})
    if main.get("type") != "sections":
        return state
    existing = main.get("sections", [])
    filtered = [s for s in existing if s.get("id") != REVIEW_SECTION_ID]
    if len(filtered) != len(existing):
        main["sections"] = filtered
        screens["main"] = main
        state["screens"] = screens
    return state
