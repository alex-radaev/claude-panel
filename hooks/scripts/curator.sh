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

# ── Run status curator (LLM-powered, updates status screen only) ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV="$PLUGIN_ROOT/.venv/bin/python3"
INPUT=$(cat)

if [ ! -f "$VENV" ]; then
    echo "$INPUT" | uv run --directory "$PLUGIN_ROOT" python -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
else
    echo "$INPUT" | PYTHONPATH="$PLUGIN_ROOT/src" "$VENV" -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
fi
