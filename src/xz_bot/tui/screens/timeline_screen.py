"""Timeline screen - chronological attack visualization."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header
from textual.containers import VerticalScroll
from rich.panel import Panel
from rich.text import Text

from xz_bot.simulator.timeline import get_timeline_events


class TimelineScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back to Menu"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="timeline-scroll"):
            yield Static(
                Panel(
                    "[bold]XZ Backdoor Attack Timeline[/]\n"
                    "[dim]CVE-2024-3094 — From first commit to discovery[/]",
                    border_style="bright_cyan",
                ),
                id="timeline-header",
            )
            events = get_timeline_events()
            for i, event in enumerate(events):
                is_last = i == len(events) - 1
                connector = "    " if is_last else "  |  "
                node_char = "(*)" if event.phase == "discovery" else "(o)"

                content = Text()
                content.append(f"  {event.date}", style=f"bold {event.phase_color}")
                content.append(f"  {node_char}\n", style=event.phase_color)
                content.append(f"  {event.title}\n", style="bold white")
                content.append(f"  {event.description}", style="dim white")

                yield Static(
                    Panel(
                        content,
                        border_style=event.phase_color,
                        padding=(0, 1),
                    )
                )
                if not is_last:
                    yield Static(
                        Text(f"  {'  |':>5}", style=event.phase_color),
                    )
        yield Footer()

    def action_go_back(self) -> None:
        self.app.switch_mode("welcome")
