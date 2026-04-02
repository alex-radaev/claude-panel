#!/usr/bin/env bash
# Session start hook: set up the 3-screen panel (main + status + ambient).
# Session-aware: creates per-session state directory and cleans up stale sessions.
# Auto-opens the panel viewer on session start (configurable via auto_open in config).

SCREENSAVERS_DIR="$HOME/.claude-panel/screensavers"
CONFIG_FILE="$HOME/.claude-panel/config.json"

# Read hook input (JSON via stdin — contains transcript_path with session ID)
INPUT=$(cat)

# Read config
FAVORITE="rain-city"
AUTO_OPEN="true"
if [ -f "$CONFIG_FILE" ]; then
    FAVORITE_CFG=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('favorite_screensaver',''))" 2>/dev/null)
    [ -n "$FAVORITE_CFG" ] && FAVORITE="$FAVORITE_CFG"
    AUTO_OPEN_CFG=$(python3 -c "import json; c=json.load(open('$CONFIG_FILE')); print(str(c.get('auto_open', True)).lower())" 2>/dev/null)
    [ -n "$AUTO_OPEN_CFG" ] && AUTO_OPEN="$AUTO_OPEN_CFG"
fi

# Resolve session ID from hook input (transcript_path), fallback to process tree
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SESSION_ID=$(python3 -c "
import json, os
try:
    data = json.loads('''$INPUT''') if '''$INPUT'''.strip() else {}
    tp = data.get('transcript_path', '')
    stem = os.path.splitext(os.path.basename(tp))[0] if tp else ''
    if len(stem) >= 32:
        print(stem)
    else:
        print('')
except Exception:
    print('')
" 2>/dev/null)

# Fallback: walk process tree
if [ -z "$SESSION_ID" ]; then
    SESSION_ID=$(uv run --directory "$PLUGIN_ROOT" python3 -c "
from claude_panel.session import get_session_id
print(get_session_id() or '')
" 2>/dev/null)
fi

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

# Check if a panel viewer is already running for THIS session
VIEWER_RUNNING=false
if [ -n "$SESSION_ID" ]; then
    if pgrep -f "claude-panel --session $SESSION_ID" > /dev/null 2>&1; then
        VIEWER_RUNNING=true
    fi
else
    # No session ID — fall back to checking for any viewer
    if pgrep -f "claude-panel --session" > /dev/null 2>&1; then
        VIEWER_RUNNING=true
    fi
fi

# Auto-open panel viewer if configured (default: true)
if [ "$AUTO_OPEN" = "true" ] && [ "$VIEWER_RUNNING" = "false" ]; then
    SESSION_FLAG=""
    [ -n "$SESSION_ID" ] && SESSION_FLAG=" --session $SESSION_ID"

    if [ "$(uname)" = "Darwin" ]; then
        CMD="cd '$PLUGIN_ROOT' && uv run claude-panel$SESSION_FLAG"
        osascript -e "
tell application \"iTerm2\"
    tell current session of current tab of current window
        set newSession to (split vertically with default profile)
        tell newSession
            write text \"$CMD\"
        end tell
    end tell
end tell
" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "CLAUDE-PANEL: Side panel opened automatically."
        else
            echo "CLAUDE-PANEL: Could not auto-open panel. Call panel_open() to launch it."
        fi
    elif [ -n "$WSL_DISTRO_NAME" ]; then
        CMD="cd '$PLUGIN_ROOT' && uv run claude-panel$SESSION_FLAG"
        wt.exe -w 0 sp -V --size 0.35 -- wsl.exe -d "$WSL_DISTRO_NAME" -- bash -lc "$CMD" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "CLAUDE-PANEL: Side panel opened automatically."
        else
            echo "CLAUDE-PANEL: Could not auto-open panel. Call panel_open() to launch it."
        fi
    else
        echo "CLAUDE-PANEL: Side panel is not running. Call panel_open() to launch it."
    fi
elif [ "$VIEWER_RUNNING" = "true" ]; then
    echo "CLAUDE-PANEL: Side panel is running."
else
    echo "CLAUDE-PANEL: Auto-open disabled. Call panel_open() to launch it."
fi

echo ""
echo "Panel uses background agents for updates (zero conversation noise)."
echo "Status screen auto-updates via Stop hook after each response."
echo "Use panel(show=\"ambient\") for screensaver, panel(show=\"main\") to check context."

# Clean up stale sessions (from previous Claude Code runs that have exited)
uv run --directory "$PLUGIN_ROOT" python3 -c "
from claude_panel.session import cleanup_stale_sessions
removed = cleanup_stale_sessions()
" 2>/dev/null
