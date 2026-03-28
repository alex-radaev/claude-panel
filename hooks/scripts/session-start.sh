#!/usr/bin/env bash
# Session start hook: set up the 3-screen panel (main + status + ambient).

SCREENSAVERS_DIR="$HOME/.claude-panel/screensavers"

# Check if the panel viewer is running
if ! pgrep -f "claude-panel" > /dev/null 2>&1; then
    echo "CLAUDE-PANEL: Side panel is not running. Call panel_open() to launch it."
else
    echo "CLAUDE-PANEL: Side panel is running."
fi

# Read config for favorite screensaver
CONFIG_FILE="$HOME/.claude-panel/config.json"
FAVORITE="rain-city"
if [ -f "$CONFIG_FILE" ]; then
    CONFIGURED=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('favorite_screensaver',''))" 2>/dev/null)
    [ -n "$CONFIGURED" ] && FAVORITE="$CONFIGURED"
fi

echo ""
echo "Panel uses background agents for updates (zero conversation noise)."
echo "Status screen auto-updates via Stop hook after each response."
echo "Use panel(show=\"ambient\") for screensaver, panel(show=\"main\") to check context."

# Reset nudge counter
echo "0" > "$HOME/.claude-panel/.nudge_state" 2>/dev/null
