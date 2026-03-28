#!/usr/bin/env bash
# Stop hook: run panel curator after Claude responds.
# Writes a loading indicator immediately, then calls the curator for real content.

STATE_FILE="$HOME/.claude-panel/state.json"

# Only run if the panel viewer is active
pgrep -f "claude-panel" > /dev/null 2>&1 || exit 0

# ── Instant: loading indicator + context usage bar ──
# Read stdin early to get transcript_path
INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('transcript_path',''))" 2>/dev/null)

if [ -f "$STATE_FILE" ]; then
    python3 -c "
import json, time, tempfile, os

state_file = '$STATE_FILE'
transcript_path = '$TRANSCRIPT'
panel_dir = os.path.dirname(state_file)

try:
    with open(state_file) as f:
        state = json.load(f)

    # Loading flag
    state['loading'] = True
    state['loading_message'] = 'Curator updating...'

    # Context usage bar (deterministic, no LLM needed)
    if transcript_path and os.path.exists(transcript_path):
        file_size = os.path.getsize(transcript_path)
        # Rough estimate: 1M token context ≈ 16MB transcript JSONL
        max_size = 16 * 1024 * 1024
        pct = min(int(file_size / max_size * 100), 100)
        size_mb = file_size / (1024 * 1024)

        # Build visual bar (40 chars wide)
        bar_width = 40
        filled = int(bar_width * pct / 100)
        bar = '\u2588' * filled + '\u2591' * (bar_width - filled)

        # Count messages in transcript
        try:
            with open(transcript_path, 'r') as f:
                msg_count = sum(1 for line in f if line.strip())
        except Exception:
            msg_count = 0

        usage_content = f'{bar}  {pct}%\n\n'
        usage_content += f'**Transcript:** {size_mb:.1f} MB  |  **Messages:** {msg_count}'

        # Update or create context section on status screen
        screens = state.get('screens', {})
        status = screens.get('status', {})
        if status.get('type') == 'sections':
            sections = status.get('sections', [])
            found = False
            for s in sections:
                if s.get('id') == 'context':
                    s['content'] = usage_content
                    found = True
                    break
            if not found:
                sections.insert(0, {'id': 'context', 'title': 'Context Usage', 'content': usage_content})
            status['sections'] = sections
            screens['status'] = status
            state['screens'] = screens

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

if [ ! -f "$VENV" ]; then
    echo "$INPUT" | uv run --directory "$PLUGIN_ROOT" python -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
else
    echo "$INPUT" | PYTHONPATH="$PLUGIN_ROOT/src" "$VENV" -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
fi
