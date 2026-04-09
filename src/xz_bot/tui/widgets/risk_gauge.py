"""Risk score gauge widget."""
from textual.widgets import Static
from rich.text import Text
from rich.panel import Panel


class RiskGauge(Static):
    """Displays a visual risk score gauge from 0-10."""

    def __init__(self, score: float = 0.0):
        self.score = score
        super().__init__()

    def update_score(self, score: float):
        self.score = min(10.0, max(0.0, score))
        self.refresh()

    def render(self):
        bar_width = 20
        filled = int((self.score / 10.0) * bar_width)
        empty = bar_width - filled

        if self.score <= 3.0:
            color = "green"
            label = "LOW RISK"
        elif self.score <= 6.0:
            color = "yellow"
            label = "MEDIUM RISK"
        elif self.score <= 8.0:
            color = "red"
            label = "HIGH RISK"
        else:
            color = "bold red"
            label = "CRITICAL"

        bar = Text()
        bar.append("  [", style="white")
        bar.append("=" * filled, style=color)
        bar.append("-" * empty, style="dim")
        bar.append("]", style="white")
        bar.append(f" {self.score:.1f}/10", style=color)
        bar.append(f"  {label}", style=color)

        return Panel(bar, title="Risk Score", border_style=color)
