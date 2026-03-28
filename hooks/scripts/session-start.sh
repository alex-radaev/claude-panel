#!/usr/bin/env bash
# Session start hook: set up the 3-screen panel (main + status + ambient).
# Session-aware: creates per-session state directory and cleans up stale sessions.

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

# Resolve session ID from parent Claude Code process
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SESSION_ID=$(python3 -c "
import json, os
pid = os.getppid()
sf = os.path.expanduser(f'~/.claude/sessions/{pid}.json')
try:
    data = json.loads(open(sf).read())
    print(data.get('sessionId', ''))
except Exception:
    print('')
" 2>/dev/null)

if [ -n "$SESSION_ID" ]; then
    # Create per-session state directory
    mkdir -p "$HOME/.claude-panel/sessions/$SESSION_ID"
    # Reset per-session nudge counter
    echo "0" > "$HOME/.claude-panel/sessions/$SESSION_ID/.nudge_state" 2>/dev/null
    # Mark as active session
    echo -n "$SESSION_ID" > "$HOME/.claude-panel/active_session" 2>/dev/null
    # Initialize ambient screen with favorite screensaver
    uv run --directory "$PLUGIN_ROOT" python3 -c "
from claude_panel.curator import read_state, write_state, ensure_multi, ensure_screen_order
from claude_panel.constants import SCREENSAVERS_DIR, CONFIG_FILE
import json
sid = '$SESSION_ID'
state = read_state(sid)
config = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
fav = config.get('favorite_screensaver', 'rain-city')
ss = SCREENSAVERS_DIR / f'{fav}.py'
if ss.exists():
    state = ensure_multi(state)
    screens = state.get('screens', {})
    order = list(state.get('screen_order', []))
    screens['ambient'] = {'type': 'screensaver', 'name': fav, 'code': ss.read_text()}
    if 'ambient' not in order:
        order.append('ambient')
    state['screens'] = screens
    state['screen_order'] = ensure_screen_order(order)
    write_state(state, sid)
" 2>/dev/null
else
    # Fallback: reset global nudge counter
    echo "0" > "$HOME/.claude-panel/.nudge_state" 2>/dev/null
fi

# Clean up stale sessions (from previous Claude Code runs that have exited)
uv run --directory "$PLUGIN_ROOT" python3 -c "
from claude_panel.session import cleanup_stale_sessions
removed = cleanup_stale_sessions()
" 2>/dev/null
