# Contributing to Claude Panel

Thanks for your interest in contributing to claude-panel. Whether you want to add a screensaver, fix a bug, or build a new feature, this guide will get you going quickly.

**The easiest way to contribute is by creating a screensaver.** No deep knowledge of the codebase required -- just a Python script that draws things to a canvas.

## Getting Started

```bash
git clone https://github.com/alex-radaev/claude-panel
cd claude-panel
uv sync
uv run claude-panel  # start the viewer
```

The viewer opens in your terminal with three screens (use arrow keys to navigate): **main**, **status**, and **ambient** (screensavers).

## Creating a Screensaver

Screensavers are standalone Python scripts that draw one animation cycle. The viewer loops them automatically.

### Where they live

Save your screensaver as `~/.claude-panel/screensavers/<name>.py`.

### What your script receives

Your script runs inside an async context with these variables pre-injected:

| Variable | Type | Description |
|----------|------|-------------|
| `canvas` | `RichLog` (Textual widget) | The drawable surface. Call `canvas.write()` to render, `canvas.clear()` to wipe. |
| `sleep` | `asyncio.sleep` | Async sleep for pacing animations. |
| `width` | `int` | Terminal width (usable columns). |
| `height` | `int` | Terminal height (usable rows). |
| `Text` | `rich.text.Text` | Rich text with styling. |
| `Panel` | `rich.panel.Panel` | Bordered panels. |
| `Table` | `rich.table.Table` | Tables and grids. |
| `Columns` | `rich.columns.Columns` | Side-by-side column layout. |
| `Syntax` | `rich.syntax.Syntax` | Syntax-highlighted code blocks. |

Your script defines **one cycle** of the animation. The viewer calls it in a loop, clearing the canvas between cycles automatically.

### Template

```python
# stars — one cycle of animation
import random

for y in range(height):
    line = Text()
    for x in range(width):
        char = random.choice([' ', '.', '*'])
        line.append(char, style="bright_cyan" if char == '*' else "dim")
    canvas.write(line)
await sleep(0.1)
```

You can use `import` statements freely -- the script runs in a full Python environment.

### Testing your screensaver

1. Save your file to `~/.claude-panel/screensavers/my-screensaver.py`
2. From a Claude Code session, call `panel(screensaver="my-screensaver")` to set it as the ambient screen
3. Or navigate to the ambient screen with arrow keys in the viewer

### Submitting your screensaver

Add the `.py` file to a `screensavers/` directory in your pull request. We will review it and include it in the default set if it fits.

## Other Ways to Contribute

- **Bug fixes** -- if something is broken, a fix is always welcome.
- **Features** -- new MCP tools, viewer improvements, curator enhancements.
- **Emoji art scripts** -- creative scripts that live in `~/.claude-panel/emoji/` and render emoji-based art on the canvas.
- **Documentation** -- clarifications, examples, typo fixes.

## Code Style

- Python 3.12+
- Async by default -- use `async def`, `await`, and async libraries
- Type hints on function signatures
- No heavy dependencies -- the project intentionally keeps its dependency footprint small (Textual, FastMCP, and the standard library cover most needs)

## Submitting a PR

1. Fork the repo and create a feature branch
2. Keep PRs small and focused -- one feature or fix per PR
3. Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`
4. Make sure the viewer still starts cleanly: `uv run claude-panel`
5. Open the PR with a brief description of what changed and why

## Code of Conduct

Be respectful and constructive. We are all here to build something useful. Assume good intent, give helpful feedback, and keep discussions focused on the work.
