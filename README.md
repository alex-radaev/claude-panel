<p align="center">
  <h1 align="center">Claude Panel</h1>
  <p align="center">
    A real-time context dashboard and ambient screensaver for Claude Code
  </p>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12+-blue.svg"></a>
  <a href="https://github.com/alex-radaev/claude-panel/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/alex-radaev/claude-panel"></a>
  <a href="https://github.com/alex-radaev/claude-panel/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/alex-radaev/claude-panel"></a>
</p>

<!-- TODO: Replace with actual hero GIF recorded with VHS -->
<!-- <p align="center"><img src="demo/hero.gif" alt="Claude Panel in action" width="800"></p> -->

A persistent side panel that lives next to your Claude Code session. It shows what Claude is working on, what decisions were made, and plays ambient terminal animations — all without adding noise to the conversation.

---

## What It Does

Claude Panel gives you **three live screens** in an iTerm2 split pane:

| Screen | What it shows | How it updates |
|--------|--------------|----------------|
| **Main** | Mood emoji, rich content, diagrams, key code | Background agents (zero conversation noise) |
| **Status** | Current task, files changed, decisions made | Stop hook + AI curator (automatic) |
| **Ambient** | Screensaver animations | `panel(screensaver="name")` |

The panel updates itself. A lightweight AI curator runs after each Claude response, reads the conversation, and updates the status dashboard. Claude can also express its "mood" with emoji art on the main screen — think of it as a non-verbal communication channel.

## Screensavers

Eight built-in ambient animations. Navigate to the ambient screen with arrow keys or `panel(show="ambient")`.

`banquet` | `city-lights` | `dvd-bounce` | `matrix`

`noir` | `rain-city` | `space-flight` | `tokyo-drift`

<!-- TODO: Replace with actual screensaver GIF grid -->
<!-- <p align="center"><img src="demo/screensavers.gif" alt="Screensaver showcase" width="600"></p> -->

Screensavers are plain Python scripts that receive a Rich canvas. [Creating your own takes ~10 lines of code.](CONTRIBUTING.md#creating-a-screensaver)

## Install

```bash
# As a Claude Code plugin (recommended)
claude plugin install claude-panel@claude-panel
```

Or manually:

```bash
git clone https://github.com/alex-radaev/claude-panel
cd claude-panel
uv sync
```

Then add to your MCP config (`~/.claude/settings.json` or `.mcp.json`).

## Usage

### Start the panel

```bash
# Via Claude — just ask it to open the panel, or:
panel_open()  # launches in iTerm2 split pane

# Manual
uv run claude-panel
```

### Panel commands

```python
panel(show="ambient")              # switch to screensaver
panel(show="main")                 # switch to main canvas
panel(screensaver="tokyo-drift")   # change screensaver
panel(show="status")               # view status dashboard
```

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit viewer |
| `<-` `->` | Cycle screens |
| `c` | Clear panel |

## How It Works

```
 Claude Code (session A)          iTerm2 Split Pane
┌──────────────────────┐         ┌──────────────────┐
│                      │         │                  │
│  MCP Server          │         │  Textual TUI     │
│  (per-session)       │         │  Viewer          │
│                      │         │                  │
└──────────┬───────────┘         └────────┬─────────┘
           │  WRITES                      │ POLLS
           └──────►  per-session   ◄──────┘
                     state.json
            ~/.claude-panel/sessions/<id>/
```

**Session isolation:** Each Claude Code session gets its own state file. Run multiple sessions simultaneously — they won't interfere with each other. The viewer automatically tracks whichever session is active.

**Update flow:**

1. **Stop hook** fires after each response — runs the AI curator (Haiku) to update the status screen
2. **Background agent** spawned by Claude — updates the main screen with mood, diagrams, or rich content
3. **Viewer** polls the state file every 300ms — re-renders on change

## Configuration

`~/.claude-panel/config.json`:

```json
{
  "model": "claude-haiku-4-5-20251001",
  "favorite_screensaver": "tokyo-drift",
  "update_every_n": 1
}
```

## Project Structure

```
claude-panel/
├── .claude-plugin/          # Plugin manifest
├── hooks/
│   ├── hooks.json           # Hook registration
│   └── scripts/
│       ├── curator.sh       # Status curator (Stop hook)
│       ├── session-start.sh # Session init + cleanup
│       └── nudge.sh         # Staleness nudge
├── src/claude_panel/
│   ├── server.py            # MCP tools (panel, screensaver, etc.)
│   ├── viewer.py            # Textual TUI viewer
│   ├── curator.py           # State helpers + AI curator
│   ├── session.py           # Per-session state isolation
│   └── constants.py         # Paths, config
└── pyproject.toml
```

## Contributing

Contributions welcome — especially new screensavers. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including a screensaver template that gets you started in ~10 lines of Python.

## License

MIT
