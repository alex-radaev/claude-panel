#!/usr/bin/env bash
# Stop hook: signal the curator daemon to update the panel.
# If the daemon isn't running, falls back to the original per-call curator.
# Session-aware: extracts session ID from transcript path.

# Only run if the panel viewer is active
pgrep -f "claude-panel" > /dev/null 2>&1 || exit 0

# ── Read hook input and extract session ID + transcript path ──
INPUT=$(cat)

SESSION_ID=$(python3 -c "
import json, sys, os
try:
    data = json.loads('''$INPUT''') if '''$INPUT'''.strip() else {}
    tp = data.get('transcript_path', '')
    stem = os.path.splitext(os.path.basename(tp))[0] if tp else ''
    print(stem if len(stem) >= 32 else '')
except Exception:
    print('')
" 2>/dev/null)

TRANSCRIPT_PATH=$(python3 -c "
import json
try:
    data = json.loads('''$INPUT''') if '''$INPUT'''.strip() else {}
    print(data.get('transcript_path', ''))
except Exception:
    print('')
" 2>/dev/null)

# ── Determine state file ──
if [ -n "$SESSION_ID" ]; then
    STATE_DIR="$HOME/.claude-panel/sessions/$SESSION_ID"
    mkdir -p "$STATE_DIR"
    STATE_FILE="$STATE_DIR/state.json"
    PID_FILE="$STATE_DIR/curator_daemon.pid"
else
    STATE_FILE="$HOME/.claude-panel/state.json"
    PID_FILE=""
fi

# ── Instant loading indicator ──
if [ -f "$STATE_FILE" ]; then
    python3 -c "
import json, time, tempfile, os
sf = '$STATE_FILE'
pd = os.path.dirname(sf)
try:
    with open(sf) as f: s = json.load(f)
    s['loading'] = True
    s['loading_message'] = 'Curator updating...'
    s['ts'] = time.time()
    fd, tmp = tempfile.mkstemp(dir=pd, suffix='.tmp')
    with open(fd, 'w') as f: json.dump(s, f)
    os.rename(tmp, sf)
except Exception: pass
" 2>/dev/null
fi

# ── Try daemon first, fall back to per-call curator ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DAEMON_RUNNING=false
if [ -n "$PID_FILE" ] && [ -f "$PID_FILE" ]; then
    DAEMON_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$DAEMON_PID" ] && kill -0 "$DAEMON_PID" 2>/dev/null; then
        DAEMON_RUNNING=true
    fi
fi

if $DAEMON_RUNNING && [ -n "$SESSION_ID" ] && [ -n "$TRANSCRIPT_PATH" ]; then
    # Nudge the daemon — just write a signal file, near-instant
    python3 -c "
import json, time
path = '$STATE_DIR/curator_nudge.json'
data = {'transcript_path': '$TRANSCRIPT_PATH', 'ts': time.time()}
open(path, 'w').write(json.dumps(data))
" 2>/dev/null
elif [ -n "$SESSION_ID" ]; then
    # Daemon died — restart it and fall back to per-call for this round
    nohup uv run --directory "$PLUGIN_ROOT" python3 -m claude_panel.curator_daemon "$SESSION_ID" \
        >> "$HOME/.claude-panel/curator.log" 2>&1 &
    # Run per-call curator for this one update while daemon warms up
    echo "$INPUT" | uv run --directory "$PLUGIN_ROOT" python -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
else
    # No session ID — fallback to per-call curator
    echo "$INPUT" | uv run --directory "$PLUGIN_ROOT" python -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
fi
