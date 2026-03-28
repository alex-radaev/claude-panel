#!/usr/bin/env bash
# Stop hook: run panel curator after Claude responds.
# Writes a loading indicator immediately, then calls the curator for real content.

STATE_FILE="$HOME/.claude-panel/state.json"

# Only run if the panel viewer is active
pgrep -f "claude-panel" > /dev/null 2>&1 || exit 0

# ── Instant loading indicator ──
INPUT=$(cat)

if [ -f "$STATE_FILE" ]; then
    python3 -c "
import json, time, tempfile, os
sf, pd = '$STATE_FILE', os.path.dirname('$STATE_FILE')
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

# ── Run status curator (LLM-powered, updates status screen only) ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Always use uv run to pick up latest source code
echo "$INPUT" | uv run --directory "$PLUGIN_ROOT" python -m claude_panel.curator \
    >> "$HOME/.claude-panel/curator.log" 2>&1
