#!/usr/bin/env bash
# Stop hook: run panel curator after Claude responds.
# Writes a loading indicator immediately, then calls the curator for real content.
# Session-aware: extracts session ID from transcript path for per-session state.

# Only run if the panel viewer is active
pgrep -f "claude-panel" > /dev/null 2>&1 || exit 0

# ── Read hook input and extract session ID ──
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

# ── Determine state file ──
if [ -n "$SESSION_ID" ]; then
    STATE_DIR="$HOME/.claude-panel/sessions/$SESSION_ID"
    mkdir -p "$STATE_DIR"
    STATE_FILE="$STATE_DIR/state.json"
else
    STATE_FILE="$HOME/.claude-panel/state.json"
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

# ── Run status curator (LLM-powered, updates status screen only) ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Always use uv run to pick up latest source code
echo "$INPUT" | uv run --directory "$PLUGIN_ROOT" python -m claude_panel.curator \
    >> "$HOME/.claude-panel/curator.log" 2>&1
