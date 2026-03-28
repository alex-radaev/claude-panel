#!/usr/bin/env bash
# Stop hook: run panel curator after Claude responds.
# Writes a loading indicator immediately, then calls the curator for real content.

STATE_FILE="$HOME/.claude-panel/state.json"

# Only run if the panel viewer is active
pgrep -f "claude-panel" > /dev/null 2>&1 || exit 0

# ── Instant loading indicator ──
# Read current state, inject a loading flag, write it back
# The viewer will show a subtle indicator
if [ -f "$STATE_FILE" ]; then
    python3 -c "
import json, time, tempfile, os
state_file = '$STATE_FILE'
panel_dir = os.path.dirname(state_file)
try:
    with open(state_file) as f:
        state = json.load(f)
    state['loading'] = True
    state['loading_message'] = 'Curator updating...'
    state['ts'] = time.time()
    fd, tmp = tempfile.mkstemp(dir=panel_dir, suffix='.tmp')
    with open(fd, 'w') as f:
        json.dump(state, f)
    os.rename(tmp, state_file)
except Exception:
    pass
" 2>/dev/null
fi

# That's it — the actual panel update is handled by a background agent
# spawned by main Claude. This hook just provides instant visual feedback.
