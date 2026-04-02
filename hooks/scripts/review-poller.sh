#!/usr/bin/env bash
# Shared background poller for GitHub review notifications.
# One instance runs across all concurrent Claude sessions.
# Self-exits when no active sessions remain.

set -euo pipefail

REVIEWS_DIR="$HOME/.claude-panel/reviews"
CONFIG_FILE="$HOME/.claude-panel/config.json"
PID_FILE="$REVIEWS_DIR/poller.pid"
STATE_FILE="$REVIEWS_DIR/state.json"
SESSIONS_DIR="$HOME/.claude-panel/sessions"

mkdir -p "$REVIEWS_DIR"

# Write our PID for lifecycle management
echo $$ > "$PID_FILE"

# Read config (poll interval + org filter)
read -r POLL_INTERVAL GH_ORG <<< $(python3 -c "
import json, os
try:
    c = json.load(open(os.path.expanduser('$CONFIG_FILE')))
    rn = c.get('review_notifications', {})
    if not isinstance(rn, dict): rn = {}
    print(rn.get('poll_interval_seconds', 120), rn.get('org', ''))
except Exception:
    print(120, '')
" 2>/dev/null)

# Clean exit: remove PID file
trap 'rm -f "$PID_FILE"; exit 0' EXIT INT TERM

while true; do
    # Self-exit when no Claude sessions remain
    SESSION_COUNT=$(find "$SESSIONS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    if [ "$SESSION_COUNT" -eq 0 ]; then
        exit 0
    fi

    # Poll GitHub for review requests (pipe to python to avoid shell quoting issues)
    GH_CMD=(gh search prs --review-requested=@me --state=open --json url,title,author,createdAt,repository --limit 20)
    [ -n "$GH_ORG" ] && GH_CMD+=(--owner "$GH_ORG")
    "${GH_CMD[@]}" 2>/dev/null | \
    python3 -c "
import json, sys, time, tempfile, os
reviews_dir = os.path.expanduser('$REVIEWS_DIR')
state_file = os.path.join(reviews_dir, 'state.json')
try:
    prs = json.load(sys.stdin)
    state = {'prs': prs, 'ts': time.time(), 'count': len(prs)}
    fd, tmp = tempfile.mkstemp(dir=reviews_dir, suffix='.tmp')
    with open(fd, 'w') as f:
        json.dump(state, f)
    os.rename(tmp, state_file)
except Exception:
    pass
" 2>/dev/null || true

    sleep "$POLL_INTERVAL"
done
