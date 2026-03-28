#!/usr/bin/env bash
# Session start hook: set up the 3-screen panel (main + status + ambient).

SCREENSAVERS_DIR="$HOME/.claude-panel/screensavers"

# Check if the panel viewer is running
if ! pgrep -f "claude-panel" > /dev/null 2>&1; then
    echo "CLAUDE-PANEL: Side panel is not running. Call panel_open() to launch it."
else
    echo "CLAUDE-PANEL: Side panel is running."
fi

# Detect favorite screensaver
FAVORITE=""
if [ -d "$SCREENSAVERS_DIR" ]; then
    if [ -f "$SCREENSAVERS_DIR/tokyo-drift.py" ]; then
        FAVORITE="tokyo-drift"
    else
        FAVORITE=$(ls "$SCREENSAVERS_DIR"/*.py 2>/dev/null | head -1 | xargs basename 2>/dev/null | sed 's/.py$//')
    fi
fi

echo ""
echo "Set up the panel's 3 screens:"
echo "  1. panel(screensaver=\"${FAVORITE:-tokyo-drift}\")  -- ambient screensaver"
echo "  2. panel(screen=\"status\", section=\"task\", content=\"...\")  -- init status dashboard"
echo "  3. panel(sections=[...])  -- show context on main as you work"
echo ""
echo "Status sections to maintain: task, files (changed), decisions (made)"
echo "Update status incrementally: panel(screen=\"status\", section=\"files\", content=\"- file.py -- what changed\")"
echo "Show screensaver when idle: panel(show=\"ambient\")"

# Reset nudge counter
echo "0" > "$HOME/.claude-panel/.nudge_state" 2>/dev/null
