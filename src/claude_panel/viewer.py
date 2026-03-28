"""Textual TUI viewer for the Claude context panel."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from rich.text import Text
from rich.panel import Panel as RichPanel
from rich.table import Table
from rich.columns import Columns
from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Markdown, RichLog, Static

from claude_panel.constants import POLL_INTERVAL, STATE_FILE


class SectionPanel(Static):
    """A single content section rendered as a bordered panel with markdown."""

    def __init__(self, section_id: str, title: str, content: str) -> None:
        super().__init__(id=f"section-{section_id}")
        self._title = title
        self._content = content

    def compose(self) -> ComposeResult:
        yield Markdown(self._content, id=f"md-{self.id}")

    def on_mount(self) -> None:
        self.border_title = self._title  # noqa: Textual reactive
        self.styles.border = ("round", "ansi_bright_cyan")
        self.styles.padding = (0, 1)
        self.styles.margin = (0, 0, 1, 0)


class WaitingMessage(Static):
    """Shown when no state file exists yet."""

    def render(self) -> Text:
        return Text.from_markup(
            "[dim]Waiting for Claude...[/]\n\n"
            "[dim italic]Start a Claude Code session with the claude-panel MCP server registered.[/]",
            justify="center",
        )

    def on_mount(self) -> None:
        self.styles.text_align = "center"
        self.styles.margin = (4, 2)


class PanelViewer(App):
    """Main Textual application for the Claude context panel."""

    TITLE = "Claude Panel"
    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary-darken-2;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        padding: 0 1;
        background: $primary-darken-3;
        color: $text-muted;
    }

    #content-area {
        padding: 1 2;
    }

    SectionPanel {
        margin-bottom: 1;
    }

    #script-container {
        padding: 1 2;
    }

    #script-canvas {
        height: 1fr;
    }

    WaitingMessage {
        height: 1fr;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear", "Clear"),
    ]

    last_ts: reactive[float] = reactive(0.0)
    current_mode: reactive[str] = reactive("waiting")
    _canvas_counter: int = 0
    _stop_screensaver: bool = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(WaitingMessage(), id="content-area")
        yield Static("Watching for updates...", id="status-bar")

    def on_mount(self) -> None:
        self.set_interval(POLL_INTERVAL, self._poll_state)

    async def _poll_state(self) -> None:
        """Check the state file for updates."""
        try:
            if not STATE_FILE.exists():
                if self.current_mode != "waiting":
                    await self._show_waiting()
                return

            raw = STATE_FILE.read_text()
            if not raw.strip():
                return

            data: dict[str, Any] = json.loads(raw)
            ts = data.get("ts", 0.0)

            if ts <= self.last_ts:
                return

            self.last_ts = ts
            mode = data.get("mode", "sections")

            # Stop any running screensaver when mode changes
            if self.current_mode == "screensaver" and mode != "screensaver":
                self._stop_screensaver = True

            if mode == "sections":
                await self._render_sections(data.get("sections", []))
            elif mode == "script":
                await self._render_script(data.get("script", {}))
            elif mode == "screensaver":
                await self._render_screensaver(data.get("screensaver", {}))

            # Update status bar
            elapsed = time.time() - ts
            if elapsed < 60:
                ago = f"{elapsed:.0f}s ago"
            else:
                ago = f"{elapsed / 60:.0f}m ago"
            self.query_one("#status-bar", Static).update(f"Last updated: {ago}")

        except (json.JSONDecodeError, KeyError, OSError):
            pass  # Transient errors during atomic write

    async def _show_waiting(self) -> None:
        """Show the waiting state."""
        self.current_mode = "waiting"
        content = self.query_one("#content-area", VerticalScroll)
        await content.remove_children()
        await content.mount(WaitingMessage())

    async def _render_sections(self, sections: list[dict[str, str]]) -> None:
        """Render sections mode."""
        self.current_mode = "sections"
        content = self.query_one("#content-area", VerticalScroll)
        await content.remove_children()

        if not sections:
            await content.mount(WaitingMessage())
            return

        for section in sections:
            sid = section.get("id", "unknown")
            title = section.get("title", "Untitled")
            body = section.get("content", "")
            panel = SectionPanel(sid, title, body)
            await content.mount(panel)

    async def _render_script(self, script: dict[str, str]) -> None:
        """Render script mode — execute a Python script with a RichLog canvas."""
        self.current_mode = "script"
        content = self.query_one("#content-area", VerticalScroll)
        await content.remove_children()

        title = script.get("title", "Script")
        code = script.get("code", "")

        self._canvas_counter += 1
        canvas = RichLog(id=f"script-canvas-{self._canvas_counter}", highlight=True, markup=True)
        canvas.border_title = title
        canvas.styles.border = ("round", "ansi_bright_magenta")
        canvas.styles.padding = (0, 1)
        canvas.styles.height = "1fr"
        await content.mount(canvas)

        # Execute the script in a worker
        self.run_worker(self._execute_script(canvas, code), exclusive=True)

    async def _render_screensaver(self, screensaver: dict[str, str]) -> None:
        """Render screensaver mode — loop a script continuously."""
        self.current_mode = "screensaver"
        self._stop_screensaver = False
        content = self.query_one("#content-area", VerticalScroll)
        await content.remove_children()

        name = screensaver.get("name", "Screensaver")
        code = screensaver.get("code", "")

        self._canvas_counter += 1
        canvas = RichLog(id=f"script-canvas-{self._canvas_counter}", highlight=True, markup=True)
        canvas.border_title = f"~ {name} ~"
        canvas.styles.border = ("round", "ansi_bright_magenta")
        canvas.styles.padding = (0, 1)
        canvas.styles.height = "1fr"
        await content.mount(canvas)

        self.query_one("#status-bar", Static).update(f"Screensaver: {name}")

        # Execute the script in a looping worker
        self.run_worker(self._execute_screensaver_loop(canvas, code), exclusive=True)

    async def _execute_screensaver_loop(self, canvas: RichLog, code: str) -> None:
        """Loop a screensaver script until interrupted."""
        term_width = self.size.width - 8
        term_height = self.size.height - 6
        namespace: dict[str, Any] = {
            "canvas": canvas,
            "sleep": asyncio.sleep,
            "width": max(term_width, 20),
            "height": max(term_height, 10),
            "Text": Text,
            "Panel": RichPanel,
            "Table": Table,
            "Columns": Columns,
            "Syntax": Syntax,
        }

        try:
            wrapped = "async def __script__():\n"
            for line in code.splitlines():
                wrapped += f"    {line}\n"
            exec(compile(wrapped, "<screensaver>", "exec"), namespace)

            while not self._stop_screensaver:
                canvas.clear()
                await namespace["__script__"]()
                await asyncio.sleep(0.1)  # brief pause between loops
        except asyncio.CancelledError:
            pass
        except Exception as e:
            canvas.write(Text(f"\n[Error] {type(e).__name__}: {e}", style="bold red"))

    async def _execute_script(self, canvas: RichLog, code: str) -> None:
        """Execute user script with canvas and rich library available."""
        # Build the script's namespace with useful imports
        # Pass terminal dimensions so scripts can fill the window
        # Account for borders, padding, header, status bar
        term_width = self.size.width - 8   # 2 padding + 2 border + margin
        term_height = self.size.height - 6  # header + status bar + borders + padding
        namespace: dict[str, Any] = {
            "canvas": canvas,
            "sleep": asyncio.sleep,
            "width": max(term_width, 20),
            "height": max(term_height, 10),
            # Rich classes for the script to use
            "Text": Text,
            "Panel": RichPanel,
            "Table": Table,
            "Columns": Columns,
            "Syntax": Syntax,
        }

        try:
            # Wrap code in an async function so `await` works
            wrapped = f"async def __script__():\n"
            for line in code.splitlines():
                wrapped += f"    {line}\n"

            exec(compile(wrapped, "<panel_script>", "exec"), namespace)
            await namespace["__script__"]()
        except Exception as e:
            canvas.write(Text(f"\n[Error] {type(e).__name__}: {e}", style="bold red"))

    async def action_clear(self) -> None:
        """Clear the panel."""
        await self._show_waiting()
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        self.last_ts = 0.0


def main():
    app = PanelViewer()
    app.run()


if __name__ == "__main__":
    main()
