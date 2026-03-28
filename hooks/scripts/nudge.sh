#!/usr/bin/env bash
# Stop hook: periodically nudge Claude to update the panel if stale.
# Fires after each assistant response. Throttled to avoid noise.
# Session-aware: uses per-session state and nudge files.

# Only nudge if the panel viewer is running
pgrep -f "claude-panel" > /dev/null 2>&1 || exit 0

# Resolve session ID from parent Claude Code process
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

# Determine state and nudge file paths
if [ -n "$SESSION_ID" ]; then
    STATE_DIR="$HOME/.claude-panel/sessions/$SESSION_ID"
    STATE_FILE="$STATE_DIR/state.json"
    NUDGE_FILE="$STATE_DIR/.nudge_state"
else
    STATE_FILE="$HOME/.claude-panel/state.json"
    NUDGE_FILE="$HOME/.claude-panel/.nudge_state"
fi

# Read and increment turn counter
COUNT=0
[ -f "$NUDGE_FILE" ] && COUNT=$(cat "$NUDGE_FILE" 2>/dev/null)
COUNT=$((COUNT + 1))
echo "$COUNT" > "$NUDGE_FILE" 2>/dev/null

# Only nudge every 5 turns
[ $((COUNT % 5)) -ne 0 ] && exit 0

# Check staleness — how long since last panel update
if [ -f "$STATE_FILE" ]; then
    TS=$(python3 -c "import json,sys; print(json.load(open('$STATE_FILE')).get('ts',0))" 2>/dev/null)
    NOW=$(python3 -c "import time; print(time.time())" 2>/dev/null)
    if [ -n "$TS" ] && [ -n "$NOW" ]; then
        AGE=$(python3 -c "print(int($NOW - $TS))" 2>/dev/null)
        if [ "$AGE" -gt 120 ]; then
            MINS=$((AGE / 60))
            echo "CLAUDE-PANEL: Panel content is ${MINS}m old. Consider updating if context has changed (panel(screen=NAME, sections=[...]))."
        fi
    fi
else
    echo "CLAUDE-PANEL: Panel is empty. Use panel(screen=NAME, sections=[...]) to show what you're working on."
fi
