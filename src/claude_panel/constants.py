from pathlib import Path

PANEL_DIR = Path.home() / ".claude-panel"
STATE_FILE = PANEL_DIR / "state.json"  # legacy global fallback
SESSIONS_DIR = PANEL_DIR / "sessions"
ACTIVE_SESSION_FILE = PANEL_DIR / "active_session"
SCREENSAVERS_DIR = PANEL_DIR / "screensavers"  # user overrides
BUNDLED_SCREENSAVERS_DIR = Path(__file__).parent / "screensavers"  # shipped with package
CONTENT_DIR = PANEL_DIR / "content"
CONFIG_FILE = PANEL_DIR / "config.json"
CURATOR_LOG = PANEL_DIR / "curator.log"
POLL_INTERVAL = 0.3  # seconds
EMOJI_DIR = PANEL_DIR / "emoji"
DEFAULT_SCREENSAVER = "rain-city"
REVIEWS_DIR = PANEL_DIR / "reviews"
REVIEW_STATE_FILE = REVIEWS_DIR / "state.json"
REVIEW_POLLER_PID = REVIEWS_DIR / "poller.pid"


def resolve_screensaver(name: str) -> Path | None:
    """Find a screensaver by name: user dir first, then bundled."""
    user_path = SCREENSAVERS_DIR / f"{name}.py"
    if user_path.exists():
        return user_path
    bundled_path = BUNDLED_SCREENSAVERS_DIR / f"{name}.py"
    if bundled_path.exists():
        return bundled_path
    return None


def list_screensavers() -> list[str]:
    """List all available screensavers (user overrides + bundled, deduplicated)."""
    names: set[str] = set()
    for d in (SCREENSAVERS_DIR, BUNDLED_SCREENSAVERS_DIR):
        if d.exists():
            names.update(p.stem for p in d.glob("*.py") if not p.name.startswith("_"))
    return sorted(names)
