<p align="center">
  <h1 align="center">Claude Panel</h1>
  <p align="center">
    Claude Code gets its own screen — it decides what you need to see
  </p>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12+-blue.svg"></a>
  <a href="https://github.com/alex-radaev/claude-panel/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/alex-radaev/claude-panel"></a>
  <a href="https://github.com/alex-radaev/claude-panel/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/alex-radaev/claude-panel"></a>
</p>

<p align="center"><img src="demo/hero.gif" alt="Panel cycling through main, status, and ambient screens" width="900"></p>
<p align="center"><em>Main screen (Claude's content) → Status dashboard → Ambient screensaver</em></p>

---

Claude Panel is a persistent TUI that sits next to your Claude Code terminal. Claude autonomously updates the panel with whatever it thinks matters — code it just wrote, a diagram, next steps, or a mood emoji. A structured dashboard tracks the current task, files changed, and key decisions, refreshing after every response. And when you're between tasks, ambient terminal screensavers keep the vibe going.

## Three Screens

| Screen | Managed by | What it shows |
|--------|-----------|---------------|
| **Main** | **Claude** | Whatever Claude thinks is useful right now — code snippets, explanations, diagrams, progress checklists, mood emoji. Full creative control. |
| **Status** | **Claude** (AI curator) | Structured dashboard: current task, files changed, decisions made. Auto-updates after every response. |
| **Ambient** | **You** | Terminal screensaver of your choice. Plays when nothing else needs your attention. |

**Claude manages the content, you manage the screensaver.** The main and status screens update automatically — Claude reads the conversation, decides what's worth pinning on screen, and writes it. No manual commands needed.

## Ambient Screensavers

Eight built-in terminal animations. Navigate with arrow keys or `panel(show="ambient")`.

<p align="center"><img src="demo/screensaver-space-flight.gif" alt="space-flight screensaver" width="900"></p>
<p align="center"><em>space-flight</em></p>

<p align="center"><img src="demo/screensaver-tokyo-drift.gif" alt="tokyo-drift screensaver" width="900"></p>
<p align="center"><em>tokyo-drift</em></p>

Also available: `rain-city` | `city-lights` | `matrix` | `noir` | `banquet` | `dvd-bounce`

Screensavers are plain Python scripts that draw to a Rich canvas. [Creating your own takes ~10 lines.](CONTRIBUTING.md#creating-a-screensaver)

## Install

```bash
# As a Claude Code plugin (recommended)
claude plugin install claude-panel@claude-panel
```

<details>
<summary>Manual installation</summary>

```bash
git clone https://github.com/alex-radaev/claude-panel
cd claude-panel
uv sync
```

Then add to your MCP config (`~/.claude/settings.json` or `.mcp.json`).

</details>

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

> **iTerm2 tip:** The panel pane may look washed out because iTerm2 dims inactive split panes by default. To fix: **Settings > Appearance > Dimming** and uncheck **Dim inactive split panes**.

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

1. **Claude responds** — a Stop hook runs the AI curator (Haiku). It reads the conversation, decides what changed, and updates the **status screen**.
2. **Claude spawns a background agent** — updates the **main screen** with whatever content is worth showing. Zero conversation noise.
3. **The viewer polls** the state file every 300ms and re-renders instantly.

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

Contributions welcome — especially new screensavers. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including a screensaver template that gets you started in ~10 lines of Python.

## License

MIT
