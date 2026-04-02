"""GitHub review notification helpers for claude-panel.

Reviews are shown in two places:
- STATUS screen: persistent section listing all PRs awaiting review
- MAIN screen: temporary mood flash when a genuinely NEW review appears
  (i.e. a PR that wasn't in the previous poll cycle)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from claude_panel.constants import CONFIG_FILE, REVIEWS_DIR, REVIEW_STATE_FILE

STATUS_SECTION_ID = "reviews"
DEFAULT_POLL_INTERVAL = 120
BASELINE_FILE = REVIEWS_DIR / "baseline.json"
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


def _format_pr_line(pr: dict[str, Any]) -> str:
    """Format a single PR as a markdown list item with link."""
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


def _build_status_section(prs: list[dict[str, Any]]) -> dict[str, str] | None:
    """Build the STATUS review section."""
    if not prs:
        return None

    lines = [_format_pr_line(pr) for pr in prs]
    return {
        "id": STATUS_SECTION_ID,
        "title": f"\U0001f4a1 Reviews ({len(prs)})",
        "content": "\n".join(lines),
    }


# ── Baseline / notification tracking ──


def _read_baseline() -> set[str]:
    """Read the set of PR URLs from the first poll (baseline)."""
    try:
        if BASELINE_FILE.exists():
            return set(json.loads(BASELINE_FILE.read_text()))
    except (json.JSONDecodeError, OSError):
        pass
    return set()


def _write_baseline(urls: set[str]) -> None:
    """Write the baseline PR URLs."""
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(list(urls)))


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


def find_unseen_reviews(prs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find reviews that are genuinely new (not in baseline and not yet notified).

    On first call, seeds the baseline with all current PRs (so nothing is "new").
    On subsequent calls, returns PRs whose URLs weren't in the baseline.
    """
    current_urls = {pr.get("url", "") for pr in prs}
    baseline = _read_baseline()

    if not baseline:
        # First run — seed baseline, nothing is new
        _write_baseline(current_urls)
        _write_notified(current_urls)
        return []

    # Update baseline to current set (so dismissed PRs don't re-trigger)
    _write_baseline(current_urls)

    notified = _read_notified()
    unseen = [pr for pr in prs if pr.get("url", "") not in notified]

    if unseen:
        notified.update(pr.get("url", "") for pr in unseen)
        # Clean up notified for PRs no longer in list
        _write_notified(notified & current_urls)

    return unseen


def _mood_code(unseen_prs: list[dict[str, Any]], context: str) -> str:
    """Generate mood display code that shows the new review alert."""
    lines_data = []
    for pr in unseen_prs[:5]:
        title = pr.get("title", "Untitled")[:50]
        repo = pr.get("repository", {}).get("nameWithOwner", "").split("/")[-1]
        author = pr.get("author", {}).get("login", "?")
        lines_data.append({"t": title, "r": repo, "a": author})

    lines_str = json.dumps(lines_data)
    context_str = json.dumps(context)
    return f'''
from rich.text import Text
from rich.align import Align

canvas.write(Text(""))
canvas.write(Align.center(Text("\U0001f4a1", style="bold")))
canvas.write(Text(""))
canvas.write(Align.center(Text({context_str}, style="bold bright_yellow")))
canvas.write(Align.center(Text("\u2501" * 30, style="dim")))
canvas.write(Text(""))

prs = {lines_str}
for pr in prs:
    line = Text("  ")
    line.append("\U0001f4a1 ", style="bold yellow")
    line.append(pr["t"], style="white")
    canvas.write(line)
    meta = Text("    ")
    meta.append(pr["r"], style="cyan")
    meta.append(" by ", style="dim")
    meta.append(pr["a"], style="green")
    canvas.write(meta)
    canvas.write(Text(""))
'''
