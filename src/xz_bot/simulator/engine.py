"""Simulator engine - orchestrates the step-by-step replay of the XZ backdoor attack."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from xz_bot.common.models import TimelineEvent
from xz_bot.simulator.build_injection import BuildInjectionStage
from xz_bot.simulator.ifunc_hijack import IFUNCHijackStage
from xz_bot.simulator.payload_extraction import PayloadExtractionStage
from xz_bot.simulator.social_engineering import SocialEngineeringStage
from xz_bot.simulator.stages import Stage
from xz_bot.simulator.timeline import get_timeline_events
from xz_bot.simulator.unauthorized_access import UnauthorizedAccessStage


class SimulatorEngine:
    """Orchestrates the step-by-step educational replay of the XZ backdoor attack."""

    def __init__(self) -> None:
        self.stages: list[Stage] = [
            SocialEngineeringStage(),
            BuildInjectionStage(),
            PayloadExtractionStage(),
            IFUNCHijackStage(),
            UnauthorizedAccessStage(),
        ]
        self.console = Console()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_all(self) -> None:
        """Run all stages sequentially with transitions."""
        self._print_header()

        for i, stage in enumerate(self.stages):
            self._run_single_stage(stage)

            # Transition between stages
            if i < len(self.stages) - 1:
                self.console.print()
                self.console.print(
                    Rule(
                        f"[dim]End of Stage {stage.order} -- Next: {self.stages[i + 1].name}[/]",
                        style="dim",
                    )
                )
                self.console.print()

        self._print_footer()

    def run_stage(self, stage_id_or_number: str | int) -> None:
        """Run a single stage by its string id or 1-based order number."""
        stage = self._resolve_stage(stage_id_or_number)
        if stage is None:
            self.console.print(
                f"[red]Stage not found: {stage_id_or_number}[/]\n"
                f"[dim]Available stages: {', '.join(s.id for s in self.stages)}[/]"
            )
            return

        self._print_header()
        self._run_single_stage(stage)
        self._print_footer()

    def get_timeline(self) -> list[TimelineEvent]:
        """Return the full timeline of events."""
        return get_timeline_events()

    def print_timeline(self) -> None:
        """Render the timeline to the console."""
        events = self.get_timeline()

        self.console.print()
        self.console.print(
            Rule("[bold]XZ Backdoor Timeline (2021 - 2024)[/]", style="magenta")
        )
        self.console.print()

        table = Table(
            show_header=True,
            header_style="bold white on dark_blue",
            expand=True,
        )
        table.add_column("Date", style="dim", width=12)
        table.add_column("Event", style="bold", ratio=1)
        table.add_column("Description", ratio=2)
        table.add_column("Phase", width=16)

        phase_colors = {
            "trust_building": "cyan",
            "injection": "yellow",
            "exploitation": "red",
            "discovery": "green",
        }

        for event in events:
            color = phase_colors.get(event.phase, "white")
            table.add_row(
                event.date,
                event.title,
                event.description,
                f"[{color}]{event.phase}[/]",
            )

        self.console.print(table)
        self.console.print()

    def list_stages(self) -> None:
        """Print a summary table of all available stages."""
        table = Table(
            title="Available Simulation Stages",
            show_header=True,
            header_style="bold white on dark_blue",
            expand=True,
        )
        table.add_column("#", width=3, justify="center")
        table.add_column("ID", style="cyan", width=22)
        table.add_column("Name", style="bold", ratio=1)
        table.add_column("Indicators", justify="center", width=12)

        for stage in self.stages:
            table.add_row(
                str(stage.order),
                stage.id,
                stage.name,
                str(len(stage.get_indicators())),
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_stage(self, stage_id_or_number: str | int) -> Stage | None:
        """Find a stage by its id string or 1-based order number."""
        if isinstance(stage_id_or_number, int):
            for stage in self.stages:
                if stage.order == stage_id_or_number:
                    return stage
            return None

        # Try as integer string first
        try:
            num = int(stage_id_or_number)
            return self._resolve_stage(num)
        except ValueError:
            pass

        # Match by id
        for stage in self.stages:
            if stage.id == stage_id_or_number:
                return stage
        return None

    def _run_single_stage(self, stage: Stage) -> None:
        """Execute explain + demonstrate + indicators for a single stage."""
        stage.explain(self.console)
        stage.demonstrate(self.console)

        # Print indicators
        indicators = stage.get_indicators()
        self.console.print()
        self.console.print(
            Rule(
                f"[bold green]Detection Indicators for Stage {stage.order}[/]",
                style="green",
            )
        )
        self.console.print()

        indicator_text = Text()
        for i, ind in enumerate(indicators, 1):
            indicator_text.append(f"  {i}. ", style="bold green")
            indicator_text.append(f"{ind}\n")

        self.console.print(
            Panel(
                indicator_text,
                title=f"[green]Indicators of Compromise[/]",
                border_style="green",
            )
        )

    def _print_header(self) -> None:
        """Print the simulator header banner."""
        self.console.print()
        self.console.print(
            Panel(
                Text.assemble(
                    ("XZ Backdoor Simulator\n", "bold white"),
                    ("CVE-2024-3094 Educational Replay\n\n", "bold red"),
                    ("This simulator walks through the five stages of the XZ Utils\n", ""),
                    ("supply-chain backdoor attack for educational purposes.\n\n", ""),
                    ("No actual malicious code is executed.", "bold green"),
                ),
                title="[bold]XZ-Bot Simulator[/]",
                border_style="blue",
                padding=(1, 4),
            )
        )

    def _print_footer(self) -> None:
        """Print the simulator footer."""
        self.console.print()
        self.console.print(
            Rule("[bold green]Simulation Complete[/]", style="green")
        )
        self.console.print()
        self.console.print(
            Panel(
                Text.assemble(
                    ("Key Takeaways:\n\n", "bold"),
                    ("1. ", "bold"),
                    ("Supply-chain attacks can target the social layer, not just code\n", ""),
                    ("2. ", "bold"),
                    ("Build systems are a critical and under-audited attack surface\n", ""),
                    ("3. ", "bold"),
                    ("Binary test fixtures deserve entropy and format analysis\n", ""),
                    ("4. ", "bold"),
                    ("Library boundaries are not security boundaries in shared address spaces\n", ""),
                    ("5. ", "bold"),
                    ("Performance anomalies can reveal sophisticated backdoors\n", ""),
                ),
                title="[green]Lessons Learned[/]",
                border_style="green",
                padding=(1, 2),
            )
        )
        self.console.print()
