"""Widget for displaying a single attack stage."""
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text


class StagePanel(Static):
    """A panel widget showing an attack stage summary."""

    def __init__(self, stage_id: str, name: str, order: int, description: str, selected: bool = False):
        self.stage_id = stage_id
        self.stage_name = name
        self.order = order
        self.description = description
        self.selected = selected
        super().__init__()

    def render(self):
        style = "bold cyan" if self.selected else "dim"
        marker = ">" if self.selected else " "
        title = f"{marker} Stage {self.order}: {self.stage_name}"
        return Panel(
            Text(self.description, style="white" if self.selected else "dim white"),
            title=title,
            border_style=style,
            padding=(0, 1),
        )
