# Claude Panel

A persistent side panel for Claude Code sessions. Three-screen TUI dashboard with background AI curator.

## Screens

| Screen | Purpose | Updated by |
|--------|---------|------------|
| **main** | Free-form canvas — plans, diagrams, explanations | Background Haiku agent |
| **status** | Structured dashboard — task, files, decisions | Stop hook + LLM curator |
| **ambient** | Screensaver animations | Direct `panel()` call |

## Install

### As a plugin (recommended)

```bash
claude plugin marketplace add /path/to/claude-panel
claude plugin install claude-panel@claude-panel
```

### Manual

```bash
cd ~/Desktop/Projects/claude-panel
uv sync
```

Add to `.mcp.json` or `~/.claude/settings.json` for MCP server access.

## Usage

### Start the viewer

```bash
# Automatic (via MCP tool)
# Claude calls panel_open() to launch in iTerm2 split

# Manual
cd ~/Desktop/Projects/claude-panel && uv run claude-panel
```

### Panel updates (zero conversation noise)

Claude updates the panel via background agents — invisible to the user:

```python
# Background Haiku agent writes to state.json (~5s)
Agent(mode="dontAsk", model="haiku", run_in_background=True,
      prompt="update panel main screen with...")

# Status auto-updates via Stop hook after every response (~15s)
```

### Direct commands (one-liners)

```python
panel(show="ambient")              # switch to screensaver
panel(screensaver="rain-city")     # change screensaver
panel(show="main")                 # switch to main
```

## Architecture

```
┌──────────────────┐     ┌──────────────────┐
│   Claude Code    │     │   iTerm2 Split   │
│                  │     │                  │
│  MCP Server      │     │  Textual TUI     │
│  (server.py)     │     │  (viewer.py)     │
└────────┬─────────┘     └────────┬─────────┘
         │  WRITES                │ POLLS
         └──────► state.json ◄────┘
              ~/.claude-panel/
```

### Update flow

1. **Stop hook** fires after each response → writes loading spinner → runs status curator (Haiku LLM)
2. **Background agent** spawned by Claude → updates main screen with rich content
3. **Viewer** polls `state.json` every 300ms → re-renders on timestamp change

### Files

```
claude-panel/
├── .claude-plugin/          # Plugin manifest + marketplace
├── hooks/
│   ├── hooks.json           # Stop hook registration
│   └── scripts/
│       ├── curator.sh       # Loading indicator + status curator
│       └── session-start.sh # Detects viewer, reminds Claude
├── src/claude_panel/
│   ├── server.py            # MCP tools (panel, screensaver, etc.)
│   ├── viewer.py            # Textual TUI with multi-screen + spinner
│   ├── curator.py           # State helpers + status LLM curator
│   └── constants.py         # Paths, poll interval
└── pyproject.toml
```

## Config

`~/.claude-panel/config.json`:

```json
{
  "model": "claude-haiku-4-5-20251001",
  "favorite_screensaver": "rain-city",
  "update_every_n": 1
}
```

## Keybindings (viewer)

| Key | Action |
|-----|--------|
| `q` | Quit |
| `←` `→` | Browse screens |
| `c` | Clear |

## Screensavers

Available: `banquet`, `city-lights`, `dvd-bounce`, `matrix`, `noir`, `rain-city`, `space-flight`, `tokyo-drift`
