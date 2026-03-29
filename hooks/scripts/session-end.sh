#!/usr/bin/env bash
# Session end hook: kill the curator daemon for this session.

# Resolve session ID
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
    PID_FILE="$HOME/.claude-panel/sessions/$SESSION_ID/curator_daemon.pid"
    if [ -f "$PID_FILE" ]; then
        DAEMON_PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$DAEMON_PID" ]; then
            kill "$DAEMON_PID" 2>/dev/null
            echo "CLAUDE-PANEL: Curator daemon stopped."
        fi
        rm -f "$PID_FILE" 2>/dev/null
    fi
fi
