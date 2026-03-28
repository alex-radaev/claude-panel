from pathlib import Path

PANEL_DIR = Path.home() / ".claude-panel"
STATE_FILE = PANEL_DIR / "state.json"
SCREENSAVERS_DIR = PANEL_DIR / "screensavers"
CONTENT_DIR = PANEL_DIR / "content"
CONFIG_FILE = PANEL_DIR / "config.json"
CURATOR_LOG = PANEL_DIR / "curator.log"
POLL_INTERVAL = 0.3  # seconds
EMOJI_DIR = PANEL_DIR / "emoji"
DEFAULT_SCREENSAVER = "rain-city"
