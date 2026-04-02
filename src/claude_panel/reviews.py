"""GitHub review notification helpers for claude-panel.

Reviews are shown in two places:
- STATUS screen: persistent section with New (≤1 day) and Pending (>1 day) categories
- MAIN screen: temporary 💡 mood takeover when a NEW review appears, auto-replaced by next curator update
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claude_panel.constants import CONFIG_FILE, REVIEWS_DIR, REVIEW_STATE_FILE

STATUS_SECTION_ID = "reviews"
DEFAULT_POLL_INTERVAL = 120
NEW_THRESHOLD_HOURS = 24
NOTIFIED_FILE = REVIEWS_DIR / "notified.json"


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


def _hours_ago(iso_str: str) -> float:
    """Return hours since the given ISO timestamp."""
    try:
        created = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - created).total_seconds() / 3600
    except Exception:
        return 999


def _time_ago(iso_str: str) -> str:
    """Convert ISO timestamp to a human-readable 'N ago' string."""
    hours = _hours_ago(iso_str)
    if hours < 1:
        return f"{int(hours * 60)}m ago"
    if hours < 24:
        return f"{int(hours)}h ago"
    return f"{int(hours / 24)}d ago"


def _format_pr_line(pr: dict[str, Any]) -> str:
    """Format a single PR as a markdown list item with 💡 and link."""
    title = pr.get("title", "Untitled")
    url = pr.get("url", "")
    repo = pr.get("repository", {}).get("nameWithOwner", "")
    author = pr.get("author", {}).get("login", "?")
    ago = _time_ago(pr.get("createdAt", ""))

    line = f"- \U0001f4a1 [{title}]({url})"
    if repo:
        line += f" \u2014 `{repo}`"
    if author:
        line += f" by @{author}"
    if ago:
        line += f" ({ago})"
    return line


def _split_reviews(prs: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    """Split PRs into new (≤1 day) and pending (>1 day)."""
    new, pending = [], []
    for pr in prs:
        hours = _hours_ago(pr.get("createdAt", ""))
        if hours <= NEW_THRESHOLD_HOURS:
            new.append(pr)
        else:
            pending.append(pr)
    return new, pending


def _build_status_section(prs: list[dict[str, Any]]) -> dict[str, str] | None:
    """Build the STATUS review section with New/Pending categories."""
    if not prs:
        return None

    new, pending = _split_reviews(prs)
    lines = []

    if new:
        lines.append(f"**New** ({len(new)})")
        lines.extend(_format_pr_line(pr) for pr in new)

    if pending:
        if new:
            lines.append("")
        lines.append(f"**Pending** ({len(pending)})")
        lines.extend(_format_pr_line(pr) for pr in pending)

    return {
        "id": STATUS_SECTION_ID,
        "title": f"\U0001f4a1 Reviews ({len(prs)})",
        "content": "\n".join(lines),
    }


def _read_notified() -> set[str]:
    """Read the set of PR URLs we've already shown a mood notification for."""
    try:
        if NOTIFIED_FILE.exists():
            return set(json.loads(NOTIFIED_FILE.read_text()))
    except (json.JSONDecodeError, OSError):
        pass
    return set()


def _write_notified(urls: set[str]) -> None:
    """Write the set of notified PR URLs."""
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    NOTIFIED_FILE.write_text(json.dumps(list(urls)))


def inject_review_notifications(state: dict[str, Any]) -> dict[str, Any]:
    """Inject review sections into STATUS and optionally flash MAIN mood."""
    if not is_enabled():
        return _strip_status(state)

    review_state = read_review_state()
    prs = review_state.get("prs", [])

    if not prs:
        return _strip_status(state)

    screens = state.get("screens", {})

    # STATUS: always show full review list (new + pending)
    status_section = _build_status_section(prs)
    if status_section:
        status = screens.get("status", {})
        if status.get("type") == "sections":
            existing = [s for s in status.get("sections", []) if s.get("id") != STATUS_SECTION_ID]
            status["sections"] = existing + [status_section]
            screens["status"] = status

    # MAIN: flash 💡 mood for genuinely unseen new reviews
    new_prs, _ = _split_reviews(prs)
    notified = _read_notified()
    unseen = [pr for pr in new_prs if pr.get("url", "") not in notified]

    if unseen:
        # Build mood context from unseen PRs
        if len(unseen) == 1:
            pr = unseen[0]
            repo = pr.get("repository", {}).get("nameWithOwner", "").split("/")[-1]
            context = f"New review: {pr.get('title', '')} ({repo})"
        else:
            context = f"{len(unseen)} new reviews need your attention"

        code = _mood_code(unseen, context)
        screens["main"] = {
            "type": "mood",
            "emoji": "\U0001f4a1",
            "context": context,
            "code": code,
        }

        # Mark as notified
        notified.update(pr.get("url", "") for pr in unseen)
        _write_notified(notified)

    # Clean up notified URLs for PRs that are no longer in the review list
    current_urls = {pr.get("url", "") for pr in prs}
    cleaned = notified & current_urls
    if cleaned != notified:
        _write_notified(cleaned)

    state["screens"] = screens
    return state


def _mood_code(unseen_prs: list[dict[str, Any]], context: str) -> str:
    """Generate mood display code that shows the new review alert."""
    lines_data = []
    for pr in unseen_prs[:5]:
        title = pr.get("title", "Untitled")[:60]
        repo = pr.get("repository", {}).get("nameWithOwner", "")
        author = pr.get("author", {}).get("login", "?")
        lines_data.append(f"{title} | {repo} | @{author}")

    lines_str = json.dumps(lines_data)
    context_str = json.dumps(context)
    return f'''
from rich.text import Text
from rich.align import Align

canvas.write(Text(""))
canvas.write(Text(""))
canvas.write(Align.center(Text("\U0001f4a1", style="bold")))
canvas.write(Text(""))
canvas.write(Align.center(Text("\u2501" * 40, style="dim")))
canvas.write(Text(""))
canvas.write(Align.center(Text({context_str}, style="bold bright_yellow")))
canvas.write(Text(""))

prs = {lines_str}
for pr in prs:
    parts = pr.split(" | ")
    title, repo, author = parts[0], parts[1], parts[2]
    line = Text()
    line.append("\U0001f4a1 ", style="bold")
    line.append(title, style="bold white")
    line.append(" \u2014 ", style="dim")
    line.append(repo, style="cyan")
    line.append(f" {{author}}", style="dim green")
    canvas.write(Align.center(line))
'''


def _strip_status(state: dict[str, Any]) -> dict[str, Any]:
    """Remove review section from STATUS."""
    screens = state.get("screens", {})
    status = screens.get("status", {})
    if status.get("type") != "sections":
        return state
    existing = status.get("sections", [])
    filtered = [s for s in existing if s.get("id") != STATUS_SECTION_ID]
    if len(filtered) != len(existing):
        status["sections"] = filtered
        screens["status"] = status
        state["screens"] = screens
    return state
