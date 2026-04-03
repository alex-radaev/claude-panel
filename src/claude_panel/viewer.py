"""Textual TUI viewer for the Claude context panel with multi-screen support."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
import webbrowser
from typing import Any

from rich.text import Text
from rich.panel import Panel as RichPanel
from rich.table import Table
from rich.columns import Columns
from rich.syntax import Syntax
from textual import events
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Header, Markdown, RichLog, Static

from claude_panel.constants import CONTENT_DIR, POLL_INTERVAL, STATE_FILE, list_screensavers, resolve_screensaver
from claude_panel.session import CLAUDE_SESSIONS_DIR, get_active_session, session_state_file

# Set by --session CLI arg; when set, viewer ignores the global active_session pointer
_pinned_session_id: str | None = None


class SectionPanel(Static):
    """A single content section rendered as a bordered panel with markdown."""

    def __init__(self, section_id: str, title: str, content: str) -> None:
        super().__init__(id=f"section-{section_id}")
        self._title = title
        self._content = content

    def compose(self) -> ComposeResult:
        yield Markdown(self._content, id=f"md-{self.id}")

    def on_mount(self) -> None:
        self.border_title = self._title
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


class ScreenBar(Static):
    """Shows available screens with the active one highlighted."""

    class ScreenClicked(Message):
        """Posted when a screen name is clicked."""

        def __init__(self, screen_name: str) -> None:
            super().__init__()
            self.screen_name = screen_name

    def __init__(self, screens: list[str], active: str) -> None:
        super().__init__(id="screen-bar")
        self._screens = screens
        self._active = active

    def _build_parts(self) -> list[tuple[str, int, int]]:
        """Build screen labels with their character offsets (name, start, end)."""
        parts: list[tuple[str, int, int]] = []
        offset = 0
        for i, name in enumerate(self._screens):
            if name == self._active:
                label = f" \u25cf {name} "
            else:
                label = f" \u25cb {name} "
            parts.append((name, offset, offset + len(label)))
            offset += len(label)
            if i < len(self._screens) - 1:
                offset += 2  # "  " separator
        return parts

    def render(self) -> Text:
        parts = []
        for name in self._screens:
            if name == self._active:
                parts.append(f"[bold bright_cyan] \u25cf {name} [/]")
            else:
                parts.append(f"[dim] \u25cb {name} [/]")
        return Text.from_markup("  ".join(parts))

    def on_click(self, event: Any) -> None:
        """Handle mouse clicks on screen names."""
        # Adjust for center alignment: calculate total bar width and offset
        parts = self._build_parts()
        if not parts:
            return
        total_width = parts[-1][2]  # end of last part
        container_width = self.size.width
        left_pad = max(0, (container_width - total_width) // 2)
        click_x = event.x - left_pad
        for name, start, end in parts:
            if start <= click_x < end:
                self.post_message(self.ScreenClicked(name))
                return

    def on_mount(self) -> None:
        self.styles.text_align = "center"
        self.styles.height = 1
        self.styles.margin = (0, 0, 1, 0)


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

    WaitingMessage {
        height: 1fr;
        content-align: center middle;
    }

    ScreenBar {
        height: 1;
        margin-bottom: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear", "Clear"),
        ("left", "prev_screen", "Prev"),
        ("right", "next_screen", "Next"),
    ]

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    last_ts: reactive[float] = reactive(0.0)
    current_mode: reactive[str] = reactive("waiting")
    _canvas_counter: int = 0
    _stop_screensaver: bool = False

    # Multi-screen state
    _screens: dict[str, Any] = {}
    _screen_order: list[str] = []
    _active_screen: str | None = None

    # Session tracking
    _current_session_id: str | None = None

    # Loading spinner state
    _loading: bool = False
    _loading_message: str = "Updating..."
    _spinner_idx: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(WaitingMessage(), id="content-area")
        yield Static("Watching for updates...", id="status-bar")

    def on_mount(self) -> None:
        self._session_miss_count = 0
        self.set_interval(POLL_INTERVAL, self._poll_state)
        self.set_interval(0.1, self._animate_spinner)
        if _pinned_session_id:
            self.set_interval(2.0, self._check_session_alive)

    async def _check_session_alive(self) -> None:
        """Exit when the pinned Claude session's process is no longer running."""
        if not CLAUDE_SESSIONS_DIR.exists():
            return
        # Find the PID file for our session and check if the process is alive
        for sf in CLAUDE_SESSIONS_DIR.glob("*.json"):
            try:
                data = json.loads(sf.read_text())
                if data.get("sessionId") == _pinned_session_id:
                    pid = int(data["pid"])
                    os.kill(pid, 0)  # doesn't kill — just checks existence
                    self._session_miss_count = 0
                    return  # process still running
            except (json.JSONDecodeError, OSError, ValueError, KeyError):
                continue
        # Session file gone or process exited — require consecutive failures before exit
        self._session_miss_count += 1
        if self._session_miss_count >= 3:
            self.exit()

    def _resolve_state_file(self) -> Any:
        """Determine which state file to poll.

        If a session was pinned via --session, always use that.
        Otherwise checks active_session; falls back to the global state.json.
        Forces re-render when the active session changes.
        """
        active_id = _pinned_session_id or get_active_session()
        if active_id != self._current_session_id:
            self._current_session_id = active_id
            self.last_ts = 0.0  # force re-render on session switch

        if active_id:
            return session_state_file(active_id)
        return STATE_FILE

    async def _poll_state(self) -> None:
        """Check the state file for updates."""
        try:
            state_file = self._resolve_state_file()

            if not state_file.exists():
                if self.current_mode != "waiting":
                    await self._show_waiting()
                return

            raw = state_file.read_text()
            if not raw.strip():
                return

            data: dict[str, Any] = json.loads(raw)
            ts = data.get("ts", 0.0)

            if ts <= self.last_ts:
                return

            self.last_ts = ts
            mode = data.get("mode", "sections")

            # Stop any running screensaver when mode changes away
            if self.current_mode in ("screensaver", "multi") and mode not in ("screensaver", "multi"):
                self._stop_screensaver = True

            if mode == "multi":
                await self._handle_multi_screen(data)
            elif mode == "sections":
                await self._render_sections(data.get("sections", []))
            elif mode == "script":
                await self._render_script(data.get("script", {}))
            elif mode == "screensaver":
                await self._render_screensaver(data.get("screensaver", {}))
            elif mode == "waiting":
                await self._show_waiting()

            # Update loading state
            self._loading = data.get("loading", False)
            self._loading_message = data.get("loading_message", "Updating...")

            # Update status bar (only if not loading — spinner handles that)
            if not self._loading:
                elapsed = time.time() - ts
                session_tag = f"[{self._current_session_id[:8]}] " if self._current_session_id else ""
                if elapsed < 60:
                    self.query_one("#status-bar", Static).update(f"{session_tag}Last updated: {elapsed:.0f}s ago")
                else:
                    self.query_one("#status-bar", Static).update(f"{session_tag}Last updated: {elapsed / 60:.0f}m ago")

        except (json.JSONDecodeError, KeyError, OSError):
            pass

    async def _animate_spinner(self) -> None:
        """Animate the loading spinner in the status bar."""
        if not self._loading:
            return
        frame = self.SPINNER_FRAMES[self._spinner_idx % len(self.SPINNER_FRAMES)]
        self._spinner_idx += 1
        self.query_one("#status-bar", Static).update(
            Text.from_markup(f"[bold bright_yellow]{frame} {self._loading_message}[/]")
        )

    async def _handle_multi_screen(self, data: dict[str, Any]) -> None:
        """Handle multi-screen mode — render the active screen."""
        self._screens = data.get("screens", {})
        self._screen_order = data.get("screen_order", [])
        new_active = data.get("active")

        if not self._screen_order:
            await self._show_waiting()
            return

        # Determine which screen to show
        if new_active and new_active in self._screens:
            self._active_screen = new_active
        elif self._active_screen not in self._screens:
            self._active_screen = self._screen_order[0]

        # Stop screensaver if switching away from a screensaver screen
        screen_data = self._screens.get(self._active_screen)
        if screen_data and screen_data.get("type") != "screensaver":
            self._stop_screensaver = True

        self.current_mode = "multi"
        await self._render_active_screen()

    async def _render_active_screen(self) -> None:
        """Render whichever screen is currently active."""
        if not self._active_screen or self._active_screen not in self._screens:
            return

        screen_data = self._screens[self._active_screen]
        screen_type = screen_data.get("type", "sections") if isinstance(screen_data, dict) else "sections"

        content = self.query_one("#content-area", VerticalScroll)
        await content.remove_children()

        # Screen bar (only if multiple screens)
        if len(self._screen_order) > 1:
            bar = ScreenBar(self._screen_order, self._active_screen)
            await content.mount(bar)

        if screen_type == "screensaver":
            await self._render_screensaver_inline(content, screen_data)
        elif screen_type == "mood":
            await self._render_mood_inline(content, screen_data)
        elif screen_type == "file":
            # Re-read the markdown file for latest content
            sections = self._load_file_sections(screen_data)
            await self._mount_sections(content, sections)
        else:
            sections = screen_data.get("sections", []) if isinstance(screen_data, dict) else screen_data
            await self._mount_sections(content, sections)

    def _load_file_sections(self, screen_data: dict[str, Any]) -> list[dict[str, str]]:
        """Load sections from a markdown file, falling back to cached sections."""
        filename = screen_data.get("file", "")
        file_path = CONTENT_DIR / filename
        if file_path.exists():
            try:
                from claude_panel.server import _parse_markdown_to_sections
                return _parse_markdown_to_sections(file_path.read_text())
            except Exception:
                pass
        return screen_data.get("sections", [])

    async def _mount_sections(self, container: VerticalScroll, sections: list[dict[str, str]]) -> None:
        """Mount section panels into a container."""
        if not sections:
            await container.mount(WaitingMessage())
        else:
            for section in sections:
                sid = section.get("id", "unknown")
                title = section.get("title", "Untitled")
                body = section.get("content", "")
                panel = SectionPanel(f"{self._active_screen}-{sid}", title, body)
                await container.mount(panel)

    async def _render_mood_inline(self, container: VerticalScroll, screen_data: dict[str, Any]) -> None:
        """Render a mood emoji script on the main screen (runs once, not looped)."""
        self._stop_screensaver = True
        code = screen_data.get("code", "")

        self._canvas_counter += 1
        canvas = RichLog(id=f"script-canvas-{self._canvas_counter}", highlight=True, markup=True)
        canvas.styles.padding = (1, 2)
        canvas.styles.height = "1fr"
        await container.mount(canvas)

        self.run_worker(self._execute_script(canvas, code), exclusive=True)

    async def _render_screensaver_inline(self, container: VerticalScroll, screen_data: dict[str, Any]) -> None:
        """Render a screensaver as an inline screen (within multi-screen mode)."""
        self._stop_screensaver = False
        name = screen_data.get("name", "Screensaver")
        code = screen_data.get("code", "")

        self._canvas_counter += 1
        canvas = RichLog(id=f"script-canvas-{self._canvas_counter}", highlight=True, markup=True)
        canvas.border_title = f"~ {name} ~"
        canvas.styles.border = ("round", "ansi_bright_magenta")
        canvas.styles.padding = (0, 1)
        canvas.styles.height = "1fr"
        await container.mount(canvas)

        hint = Static(Text.from_markup("[dim]\u2191 \u2193 cycle screensavers[/]"))
        hint.styles.text_align = "center"
        hint.styles.margin = (0, 0)
        await container.mount(hint)

        self.run_worker(self._execute_screensaver_loop(canvas, code), exclusive=True)

    async def _show_waiting(self) -> None:
        """Show the waiting state."""
        self.current_mode = "waiting"
        self._screens = {}
        self._screen_order = []
        self._active_screen = None
        content = self.query_one("#content-area", VerticalScroll)
        await content.remove_children()
        await content.mount(WaitingMessage())

    async def _render_sections(self, sections: list[dict[str, str]]) -> None:
        """Render single-screen sections mode (backward compatible)."""
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
        """Render script mode -- execute a Python script with a RichLog canvas."""
        self.current_mode = "script"
        self._stop_screensaver = True
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

        self.run_worker(self._execute_script(canvas, code), exclusive=True)

    async def _render_screensaver(self, screensaver: dict[str, str]) -> None:
        """Render standalone screensaver mode (legacy screensaver_play)."""
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
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            canvas.write(Text(f"\n[Error] {type(e).__name__}: {e}", style="bold red"))

    async def _execute_script(self, canvas: RichLog, code: str) -> None:
        """Execute user script with canvas and rich library available."""
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

            exec(compile(wrapped, "<panel_script>", "exec"), namespace)
            await namespace["__script__"]()
        except Exception as e:
            canvas.write(Text(f"\n[Error] {type(e).__name__}: {e}", style="bold red"))

    # ── Link handling ──

    async def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        """Open markdown links in the default browser."""
        if event.href.startswith(("http://", "https://")):
            webbrowser.open(event.href)

    # ── Key handling ──

    def on_key(self, event: events.Key) -> None:
        """Intercept up/down to cycle screensavers when on a screensaver screen."""
        if event.key in ("up", "down"):
            screen_data = self._screens.get(self._active_screen)
            if screen_data and screen_data.get("type") == "screensaver":
                self._cycle_screensaver(-1 if event.key == "up" else 1)
                event.prevent_default()
                event.stop()

    # ── Screen navigation (keyboard + mouse) ──

    async def on_screen_bar_screen_clicked(self, event: ScreenBar.ScreenClicked) -> None:
        """Handle mouse click on a screen name in the bar."""
        name = event.screen_name
        if self.current_mode != "multi" or name not in self._screen_order:
            return
        if name == self._active_screen:
            return
        self._active_screen = name
        self._stop_screensaver = True
        await asyncio.sleep(0.05)
        self._stop_screensaver = False
        await self._render_active_screen()

    async def action_prev_screen(self) -> None:
        """Navigate to previous screen."""
        if self.current_mode != "multi" or len(self._screen_order) <= 1:
            return
        idx = self._screen_order.index(self._active_screen) if self._active_screen in self._screen_order else 0
        idx = (idx - 1) % len(self._screen_order)
        self._active_screen = self._screen_order[idx]
        self._stop_screensaver = True
        await asyncio.sleep(0.05)  # let screensaver worker stop
        self._stop_screensaver = False
        await self._render_active_screen()

    async def action_next_screen(self) -> None:
        """Navigate to next screen."""
        if self.current_mode != "multi" or len(self._screen_order) <= 1:
            return
        idx = self._screen_order.index(self._active_screen) if self._active_screen in self._screen_order else 0
        idx = (idx + 1) % len(self._screen_order)
        self._active_screen = self._screen_order[idx]
        self._stop_screensaver = True
        await asyncio.sleep(0.05)
        self._stop_screensaver = False
        await self._render_active_screen()

    def _cycle_screensaver(self, direction: int) -> None:
        """Switch the ambient screen to the next/prev screensaver."""
        if self.current_mode != "multi":
            return
        screen_data = self._screens.get(self._active_screen)
        if not screen_data or screen_data.get("type") != "screensaver":
            return
        available = list_screensavers()
        if len(available) <= 1:
            return
        current = screen_data.get("name", "")
        try:
            idx = available.index(current)
        except ValueError:
            idx = 0
        idx = (idx + direction) % len(available)
        new_name = available[idx]
        path = resolve_screensaver(new_name)
        if not path:
            return
        # Update state file so the poll loop picks it up
        state_file = self._resolve_state_file()
        try:
            raw = state_file.read_text()
            state = json.loads(raw)
            state["screens"][self._active_screen] = {
                "type": "screensaver",
                "name": new_name,
                "code": path.read_text(),
            }
            state["active"] = self._active_screen
            state["ts"] = time.time()
            fd, tmp = tempfile.mkstemp(dir=str(state_file.parent), suffix=".tmp")
            with open(fd, "w") as f:
                json.dump(state, f)
            os.rename(tmp, str(state_file))
            self.run_worker(self._render_active_screen(), exclusive=True)
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    async def action_clear(self) -> None:
        """Clear the panel (active session or global)."""
        await self._show_waiting()
        state_file = self._resolve_state_file()
        if state_file.exists():
            state_file.unlink()
        self.last_ts = 0.0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Claude Panel viewer")
    parser.add_argument("--session", help="Pin viewer to a specific session ID")
    args = parser.parse_args()

    global _pinned_session_id
    _pinned_session_id = args.session

    app = PanelViewer()
    app.run()


if __name__ == "__main__":
    main()
