#!/usr/bin/env bash
# Session start hook: set up the 3-screen panel (main + status + ambient).
# Session-aware: creates per-session state directory and cleans up stale sessions.
# Auto-opens the panel viewer on session start (configurable via auto_open in config).

SCREENSAVERS_DIR="$HOME/.claude-panel/screensavers"
CONFIG_FILE="$HOME/.claude-panel/config.json"

# Skip panel setup for agent team members (they don't need their own panel)
if [ -n "$CLAUDE_CODE_TEAM_NAME" ]; then
    echo "CLAUDE-PANEL: Skipping panel for team member ($CLAUDE_CODE_TEAM_NAME)."
    exit 0
fi

# Read hook input (JSON via stdin — contains transcript_path with session ID)
INPUT=$(cat)

# Read config
FAVORITE="rain-city"
AUTO_OPEN="true"
REVIEW_ENABLED="true"
if [ -f "$CONFIG_FILE" ]; then
    FAVORITE_CFG=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('favorite_screensaver',''))" 2>/dev/null)
    [ -n "$FAVORITE_CFG" ] && FAVORITE="$FAVORITE_CFG"
    AUTO_OPEN_CFG=$(python3 -c "import json; c=json.load(open('$CONFIG_FILE')); print(str(c.get('auto_open', True)).lower())" 2>/dev/null)
    [ -n "$AUTO_OPEN_CFG" ] && AUTO_OPEN="$AUTO_OPEN_CFG"
    REVIEW_ENABLED_CFG=$(python3 -c "
import json
c = json.load(open('$CONFIG_FILE'))
rn = c.get('review_notifications', {})
print(str(rn.get('enabled', True) if isinstance(rn, dict) else rn).lower())
" 2>/dev/null)
    [ -n "$REVIEW_ENABLED_CFG" ] && REVIEW_ENABLED="$REVIEW_ENABLED_CFG"
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

# Detect spawned agent: check if any ancestor process has --parent-session-id in its
# command line. Claude Code passes this flag to spawned team agents.
IS_AGENT=false
PID_WALK=$$
while [ "$PID_WALK" -gt 1 ] 2>/dev/null; do
    PARENT_PID=$(ps -o ppid= -p "$PID_WALK" 2>/dev/null | tr -d ' ')
    [ -z "$PARENT_PID" ] && break
    CMD_LINE=$(ps -o args= -p "$PARENT_PID" 2>/dev/null)
    if echo "$CMD_LINE" | grep -q -- "--parent-session-id"; then
        IS_AGENT=true
        break
    fi
    PID_WALK="$PARENT_PID"
done

if [ "$IS_AGENT" = "true" ]; then
    echo "CLAUDE-PANEL: Skipping panel for spawned agent."
    exit 0
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
        CMD="cd '$PLUGIN_ROOT' && uv run claude-panel$SESSION_FLAG; exit"
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
        CMD="cd '$PLUGIN_ROOT' && uv run claude-panel$SESSION_FLAG; exit"
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

# Start review notification poller if enabled and not already running
if [ "$REVIEW_ENABLED" = "true" ]; then
    POLLER_PID_FILE="$HOME/.claude-panel/reviews/poller.pid"
    POLLER_RUNNING=false
    if [ -f "$POLLER_PID_FILE" ]; then
        POLLER_PID=$(cat "$POLLER_PID_FILE" 2>/dev/null)
        if [ -n "$POLLER_PID" ] && kill -0 "$POLLER_PID" 2>/dev/null; then
            POLLER_RUNNING=true
        fi
    fi
    if [ "$POLLER_RUNNING" = "false" ]; then
        nohup bash "$SCRIPT_DIR/review-poller.sh" > /dev/null 2>&1 &
    fi
fi
