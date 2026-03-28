from pathlib import Path

PANEL_DIR = Path.home() / ".claude-panel"
STATE_FILE = PANEL_DIR / "state.json"
POLL_INTERVAL = 0.3  # seconds
