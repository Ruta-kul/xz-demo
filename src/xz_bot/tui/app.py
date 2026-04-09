"""XZ-Bot Terminal User Interface - main application."""
from pathlib import Path

from textual.app import App

from xz_bot.tui.screens.welcome import WelcomeScreen
from xz_bot.tui.screens.walkthrough import WalkthroughScreen
from xz_bot.tui.screens.scanner_screen import ScannerScreen
from xz_bot.tui.screens.timeline_screen import TimelineScreen

CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"


class XZBotApp(App):
    """XZ-Bot Interactive Security Lab."""

    TITLE = "XZ-Bot | CVE-2024-3094 Interactive Lab"
    SUB_TITLE = "Agentic AI Vulnerability Scanner & Backdoor Demo"
    CSS_PATH = CSS_PATH

    MODES = {
        "welcome": WelcomeScreen,
        "walkthrough": WalkthroughScreen,
        "scanner": ScannerScreen,
        "timeline": TimelineScreen,
    }

    def on_mount(self) -> None:
        self.switch_mode("welcome")


def run_tui():
    """Launch the TUI application."""
    app = XZBotApp()
    app.run()
