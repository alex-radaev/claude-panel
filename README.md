<p align="center">
  <h1 align="center">Claude Panel</h1>
  <p align="center">
    A side panel where Claude shows you what it's thinking — plus ambient screensavers
  </p>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12+-blue.svg"></a>
  <a href="https://github.com/alex-radaev/claude-panel/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/alex-radaev/claude-panel"></a>
  <a href="https://github.com/alex-radaev/claude-panel/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/alex-radaev/claude-panel"></a>
</p>

<p align="center"><img src="demo/split-pane.png" alt="Claude Code + Panel — ambient screensaver running" width="900"></p>

Claude Code is great, but the conversation scrolls fast. What was the last decision? Which files changed? What's Claude working on right now?

**Claude Panel** is a persistent TUI that sits next to your terminal. Claude decides what to show — summaries, explanations, next steps, diagrams, code highlights, or just a mood emoji. It's a second communication channel that doesn't clutter the conversation.

---

## Three Screens

| Screen | Managed by | What it shows |
|--------|-----------|---------------|
| **Main** | **Claude** | Whatever Claude thinks is useful right now — explanations, key code, architecture diagrams, progress checklists, mood emoji. Claude has full creative control. |
| **Status** | **Claude** (AI curator) | Structured dashboard: current task, files changed, decisions made. Auto-updates after every response via a lightweight Haiku curator. |
| **Ambient** | **You** | Terminal screensaver of your choice. Plays when nothing else needs your attention. |

The key idea: **Claude manages the content, you manage the screensaver.** The main and status screens update automatically — Claude reads the conversation, decides what's worth pinning on screen, and writes it. No manual commands needed.

### Main Screen — Claude's Canvas

Claude uses the main screen to show you whatever is most relevant:

- Working on auth? It shows the key function signature and a fire emoji
- Debugging? The error message and current hypothesis
- Multi-step task? A progress checklist with checked items
- Just vibing? A mood emoji

<p align="center"><img src="demo/main-screen.png" alt="Main screen with rich content" width="600"></p>

### Status Screen — Structured Dashboard

After every Claude response, a lightweight AI curator reads the conversation and updates three fields:

- **Current Task** — what Claude is working on right now
- **Files Changed** — which files were touched and why
- **Decisions** — non-obvious choices made and the reasoning

This happens automatically via a Stop hook. Zero effort from you.

<p align="center"><img src="demo/status-screen.png" alt="Status screen dashboard" width="600"></p>

### Ambient Screen — Your Screensaver

Eight built-in terminal animations. Navigate with arrow keys or `panel(show="ambient")`.

<p align="center"><img src="demo/screensavers.gif" alt="Screensaver showcase" width="600"></p>

`banquet` | `city-lights` | `dvd-bounce` | `matrix` | `noir` | `rain-city` | `space-flight` | `tokyo-drift`

Screensavers are plain Python scripts that draw to a Rich canvas. [Creating your own takes ~10 lines.](CONTRIBUTING.md#creating-a-screensaver)

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

The panel opens in an iTerm2 split pane. Ask Claude to open it, or:

```bash
# From Claude Code
panel_open()

# Manual
uv run claude-panel
```

Once running, Claude takes over. The main and status screens update on their own. You can switch views:

```python
panel(show="ambient")              # switch to screensaver
panel(show="main")                 # switch to main canvas
panel(show="status")               # switch to status dashboard
panel(screensaver="tokyo-drift")   # change screensaver
```

| Key | Action |
|-----|--------|
| `q` | Quit viewer |
| `<-` `->` | Cycle screens |
| `c` | Clear panel |

## How It Works

```
 Claude Code session              iTerm2 Split Pane
┌──────────────────────┐         ┌──────────────────┐
│                      │         │                  │
│  Main Claude         │         │  Textual TUI     │
│  + Background agents │         │  Viewer          │
│  + Stop hook curator │         │                  │
│                      │         │                  │
└──────────┬───────────┘         └────────┬─────────┘
           │  WRITES                      │ POLLS
           └──────►  per-session   ◄──────┘
                     state.json
            ~/.claude-panel/sessions/<id>/
```

1. **Claude responds** — a Stop hook fires and runs the AI curator (Haiku). It reads the conversation, decides what changed, and updates the status screen.
2. **Claude spawns a background agent** — updates the main screen with whatever content Claude thinks is worth showing. This runs silently with zero conversation noise.
3. **The viewer polls** the session state file every 300ms and re-renders on change.

**Session isolation:** Each Claude Code session gets its own state. Run multiple sessions — they don't interfere. The viewer tracks whichever session is active.

## Configuration

`~/.claude-panel/config.json`:

```json
{
  "model": "claude-haiku-4-5-20251001",
  "favorite_screensaver": "tokyo-drift",
  "update_every_n": 1
}
```

## Contributing

Contributions welcome — especially new screensavers. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including a screensaver template.

## License

MIT
