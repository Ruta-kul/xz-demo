"""Welcome screen for XZ-Bot TUI."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header
from textual.containers import Center, Vertical
from rich.text import Text
from rich.panel import Panel


BANNER = r"""
 __  ______    ____        _
 \ \/ /__  /  | __ )  ___ | |_
  \  /  / /   |  _ \ / _ \| __|
  /  \ / /_   | |_) | (_) | |_
 /_/\_\/____|  |____/ \___/ \__|

  CVE-2024-3094 Interactive Lab
  Agentic AI Vulnerability Scanner
"""


class WelcomeScreen(Screen):
    BINDINGS = [
        ("1", "switch_screen('walkthrough')", "Attack Walkthrough"),
        ("2", "switch_screen('scanner')", "Vulnerability Scanner"),
        ("3", "switch_screen('timeline')", "Attack Timeline"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="welcome-box"):
                yield Static(
                    Panel(
                        Text(BANNER, style="bold cyan", justify="center"),
                        border_style="bright_cyan",
                        padding=(1, 2),
                    ),
                    id="banner",
                )
                yield Static(
                    Panel(
                        Text.from_markup(
                            "[bold white]Choose a module:[/]\n\n"
                            "  [bold cyan][1][/] Attack Walkthrough  - Step-by-step XZ backdoor replay\n"
                            "  [bold cyan][2][/] Vulnerability Scanner - Agentic AI code analysis\n"
                            "  [bold cyan][3][/] Attack Timeline     - Chronological event map\n"
                            "  [bold cyan][q][/] Quit\n"
                        ),
                        title="Modules",
                        border_style="green",
                        padding=(1, 2),
                    ),
                    id="menu",
                )
                yield Static(
                    Text(
                        "Educational tool only. All samples are inert and safe.",
                        style="dim italic",
                        justify="center",
                    ),
                    id="disclaimer",
                )
        yield Footer()

    def action_switch_screen(self, screen_name: str) -> None:
        self.app.switch_mode(screen_name)

    def action_quit(self) -> None:
        self.app.exit()
