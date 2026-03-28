# Claude Panel

A persistent side panel for Claude Code. MCP server exposes tools that let Claude push content to a Textual TUI running in an adjacent iTerm2 pane.

## What it does

- **Status dashboard** — goal, progress, changed files, assumptions
- **Rich explanations** — markdown with code blocks, diagrams
- **Animations** — run Python scripts that render dynamic content in the panel

## Setup

### 1. Install

```bash
cd ~/Desktop/Projects/claude-panel
uv sync
```

### 2. iTerm2 config

- **Vertical split**: `Cmd + D` to create a side-by-side layout
- **Disable dimming**: iTerm2 > Settings > Appearance > Dimming > uncheck "Dim inactive split panes"
- Switch between panes: `Cmd + Option + Arrow`

### 3. Start the viewer

In the right pane:

```bash
cd ~/Desktop/Projects/claude-panel && uv run claude-panel
```

### 4. Register MCP server

The `.mcp.json` in this project auto-registers with Claude Code when you work from this directory. For global access, add to `~/.claude/settings.json`.

## Tools

### `panel(sections)`

Static content display. Each call replaces the entire panel.

```json
{
  "sections": [
    {"id": "goal", "title": "Goal", "content": "Build auth middleware"},
    {"id": "progress", "title": "Progress", "content": "- [x] Read code\n- [ ] Write tests"}
  ]
}
```

Pass an empty list to clear.

### `panel_script(code, title)`

Run a Python script inside the viewer. The script receives:

- `canvas` — RichLog widget (`canvas.write(...)`, `canvas.clear()`)
- `sleep` — async sleep for timing
- `width`, `height` — actual panel dimensions in characters
- Rich classes: `Text`, `Panel`, `Table`, `Columns`, `Syntax`

```json
{
  "code": "for i in range(5):\n    canvas.write(f'Step {i+1}')\n    await sleep(0.5)",
  "title": "Demo"
}
```

## Keybindings

| Key | Action |
|-----|--------|
| `q` | Quit viewer |
| `c` | Clear panel |

## Architecture

```
Claude Code --stdio--> MCP Server (panel tool) --JSON file--> Textual Viewer (iTerm2 pane)
```

IPC is a shared JSON file at `~/.claude-panel/state.json` (atomic write via temp+rename). The viewer polls every 300ms.
