"""Walkthrough screen - guided attack stage replay."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, RichLog, ListView, ListItem, Label
from textual.containers import Horizontal, Vertical
from rich.text import Text
from rich.panel import Panel

from xz_bot.simulator.engine import SimulatorEngine


class WalkthroughScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back to Menu"),
        ("left", "prev_stage", "Previous"),
        ("right", "next_stage", "Next"),
        ("d", "demonstrate", "Demo"),
    ]

    def __init__(self):
        super().__init__()
        self.engine = SimulatorEngine()
        self.current_stage_idx = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="walkthrough-layout"):
            with Vertical(id="stage-list"):
                yield Static(
                    Panel("[bold]Attack Stages[/]", border_style="cyan"),
                    id="stage-header",
                )
                yield ListView(
                    *[
                        ListItem(Label(f"  {s.order}. {s.name}"), id=f"stage-{i}")
                        for i, s in enumerate(self.engine.stages)
                    ],
                    id="stages",
                )
            with Vertical(id="stage-detail"):
                yield RichLog(highlight=True, markup=True, id="stage-output", wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self._show_stage(0)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = self.query_one("#stages", ListView).index
        if idx is not None:
            self.current_stage_idx = idx
            self._show_stage(idx)

    def action_prev_stage(self) -> None:
        if self.current_stage_idx > 0:
            self.current_stage_idx -= 1
            self.query_one("#stages", ListView).index = self.current_stage_idx
            self._show_stage(self.current_stage_idx)

    def action_next_stage(self) -> None:
        if self.current_stage_idx < len(self.engine.stages) - 1:
            self.current_stage_idx += 1
            self.query_one("#stages", ListView).index = self.current_stage_idx
            self._show_stage(self.current_stage_idx)

    def action_demonstrate(self) -> None:
        log = self.query_one("#stage-output", RichLog)
        log.write("")
        log.write(Panel("[bold yellow]-- DEMONSTRATION --[/]", border_style="yellow"))
        stage = self.engine.stages[self.current_stage_idx]
        stage.demonstrate(log)

    def _show_stage(self, idx: int) -> None:
        stage = self.engine.stages[idx]
        log = self.query_one("#stage-output", RichLog)
        log.clear()
        stage.explain(log)

    def action_go_back(self) -> None:
        self.app.switch_mode("welcome")
