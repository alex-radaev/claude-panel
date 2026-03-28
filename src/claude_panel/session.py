"""Session identification for claude-panel.

Resolves the current Claude Code session ID by walking up the process tree
to find the parent Claude Code process, then reading its session metadata
from ~/.claude/sessions/<pid>.json.

Each session gets isolated state in ~/.claude-panel/sessions/<session-id>/.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

CLAUDE_SESSIONS_DIR = Path.home() / ".claude" / "sessions"


def _get_ppid(pid: int) -> Optional[int]:
    """Get parent PID of a given process (macOS/Linux)."""
    try:
        result = subprocess.run(
            ["ps", "-o", "ppid=", "-p", str(pid)],
            capture_output=True, text=True, timeout=2,
        )
        return int(result.stdout.strip()) if result.stdout.strip() else None
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return None


def _find_claude_pid() -> Optional[int]:
    """Walk up the process tree to find the Claude Code parent process."""
    pid = os.getpid()
    visited: set[int] = set()

    while pid and pid > 1 and pid not in visited:
        visited.add(pid)
        ppid = os.getppid() if pid == os.getpid() else _get_ppid(pid)
        if ppid is None:
            break
        # Check if this PID has a Claude session file
        session_file = CLAUDE_SESSIONS_DIR / f"{ppid}.json"
        if session_file.exists():
            return ppid
        pid = ppid
    return None


def get_session_id() -> Optional[str]:
    """Get the Claude Code session ID for the current process tree."""
    claude_pid = _find_claude_pid()
    if claude_pid is None:
        return None
    return get_session_id_from_pid(claude_pid)


def get_session_id_from_pid(pid: int) -> Optional[str]:
    """Look up session ID from a known Claude Code PID."""
    session_file = CLAUDE_SESSIONS_DIR / f"{pid}.json"
    if not session_file.exists():
        return None
    try:
        data = json.loads(session_file.read_text())
        return data.get("sessionId")
    except (json.JSONDecodeError, OSError):
        return None


def get_session_id_from_transcript(transcript_path: str) -> Optional[str]:
    """Extract session ID from transcript path.

    Claude Code transcript files are named <session-uuid>.jsonl,
    so the stem is the session ID.
    """
    if not transcript_path:
        return None
    p = Path(transcript_path)
    if p.suffix == ".jsonl" and len(p.stem) >= 32:
        return p.stem
    return None


def session_state_dir(session_id: str) -> Path:
    """Return the state directory for a given session."""
    from claude_panel.constants import SESSIONS_DIR
    return SESSIONS_DIR / session_id


def session_state_file(session_id: str) -> Path:
    """Return the state file path for a given session."""
    return session_state_dir(session_id) / "state.json"


def set_active_session(session_id: str) -> None:
    """Mark a session as the currently active one (atomic write)."""
    from claude_panel.constants import ACTIVE_SESSION_FILE, PANEL_DIR
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(PANEL_DIR), suffix=".tmp")
    try:
        with open(fd, "w") as f:
            f.write(session_id)
        os.rename(tmp, str(ACTIVE_SESSION_FILE))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def get_active_session() -> Optional[str]:
    """Read the currently active session ID."""
    from claude_panel.constants import ACTIVE_SESSION_FILE
    try:
        return ACTIVE_SESSION_FILE.read_text().strip() if ACTIVE_SESSION_FILE.exists() else None
    except OSError:
        return None


def list_sessions() -> list[str]:
    """List all session IDs that have state directories."""
    from claude_panel.constants import SESSIONS_DIR
    if not SESSIONS_DIR.exists():
        return []
    return [
        d.name for d in SESSIONS_DIR.iterdir()
        if d.is_dir() and (d / "state.json").exists()
    ]


def cleanup_stale_sessions() -> list[str]:
    """Remove session state for sessions whose Claude Code process has exited."""
    removed: list[str] = []
    # Build set of active session IDs from Claude's session files
    active_ids: set[str] = set()
    if CLAUDE_SESSIONS_DIR.exists():
        for sf in CLAUDE_SESSIONS_DIR.glob("*.json"):
            try:
                data = json.loads(sf.read_text())
                sid = data.get("sessionId")
                if sid:
                    active_ids.add(sid)
            except (json.JSONDecodeError, OSError):
                continue

    for session_id in list_sessions():
        if session_id not in active_ids:
            sdir = session_state_dir(session_id)
            shutil.rmtree(sdir, ignore_errors=True)
            removed.append(session_id)
    return removed
