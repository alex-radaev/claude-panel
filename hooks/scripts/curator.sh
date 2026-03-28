#!/usr/bin/env bash
# UserPromptSubmit hook: run panel curator before Claude responds.
# Reads hook JSON from stdin, calls the curator Python module.

# Only run if the panel viewer is active
pgrep -f "claude-panel" > /dev/null 2>&1 || exit 0

# Find the project venv
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV="$PLUGIN_ROOT/.venv/bin/python3"

# Fallback: try uv run
if [ ! -f "$VENV" ]; then
    # Read stdin and pass to curator via uv
    INPUT=$(cat)
    echo "$INPUT" | uv run --directory "$PLUGIN_ROOT" python -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
else
    INPUT=$(cat)
    echo "$INPUT" | PYTHONPATH="$PLUGIN_ROOT/src" "$VENV" -m claude_panel.curator \
        >> "$HOME/.claude-panel/curator.log" 2>&1
fi
