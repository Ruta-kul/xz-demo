"""Stage 1: Social Engineering - Building trust to gain maintainer access."""

from __future__ import annotations

import json
from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from xz_bot.common.models import AttackStage
from xz_bot.simulator.stages import Stage

_SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples" / "git_history"

_PHASE_STYLES = {
    "trust_building": "cyan",
    "injection": "yellow",
    "exploitation": "red",
    "discovery": "green",
}


class SocialEngineeringStage(Stage):
    """Stage 1: How 'Jia Tan' built trust over two years with small patches."""

    id = "social_engineering"
    name = "Social Engineering & Trust Building"
    order = 1

    # ------------------------------------------------------------------
    # explain
    # ------------------------------------------------------------------
    def explain(self, console: Console) -> None:
        console.print()
        console.print(
            Rule(
                "[bold magenta]Stage 1: Social Engineering & Trust Building[/]",
                style="magenta",
            )
        )
        console.print()

        overview = Markdown(
            "The XZ backdoor began not with code, but with **people**. An actor "
            "using the pseudonym **Jia Tan** spent over **two years** cultivating "
            "trust within the XZ Utils project before injecting any malicious code.\n\n"
            "This is a textbook example of a *long-con supply-chain attack* where "
            "the social layer is exploited before any technical vulnerability."
        )
        console.print(Panel(overview, title="Overview", border_style="blue"))

        # --- Phase breakdown ---
        console.print()
        console.print("[bold cyan]The Campaign Phases[/]")
        console.print()

        phases = Table(show_header=True, header_style="bold white on dark_blue", expand=True)
        phases.add_column("Phase", style="bold", width=22)
        phases.add_column("Timeframe", width=20)
        phases.add_column("Activities")
        phases.add_row(
            "[cyan]1. Introduction[/]",
            "Jan 2021 - Jun 2021",
            "Typo fixes, documentation patches, small test additions. "
            "Establishing a presence on the mailing list.",
        )
        phases.add_row(
            "[cyan]2. Credibility[/]",
            "Jul 2021 - May 2022",
            "CRC code cleanups, CMake improvements, legitimate bug fixes. "
            "Becoming a recognized and trusted contributor.",
        )
        phases.add_row(
            "[yellow]3. Pressure[/]",
            "Jun 2022 - Sep 2022",
            "Sockpuppet accounts (Dennis Ens, Jigar Kumar) pressure the "
            "sole maintainer Lasse Collin to add a co-maintainer.",
        )
        phases.add_row(
            "[red]4. Takeover[/]",
            "Oct 2022 - 2023",
            "Jia Tan gains commit access and begins modifying build "
            "infrastructure and test fixtures.",
        )
        console.print(phases)
        console.print()

        # --- Key social engineering techniques ---
        techniques = Panel(
            Text.assemble(
                ("Incremental scope expansion", "bold"),
                " - progressing from docs to tests to build system to core code\n",
                ("Manufactured urgency", "bold"),
                " - sockpuppet accounts complaining about slow maintenance\n",
                ("Exploiting burnout", "bold"),
                " - targeting a solo maintainer under pressure\n",
                ("Long time horizon", "bold"),
                " - 2+ years of patience before any malicious action\n",
                ("Identity obfuscation", "bold"),
                " - VPN-only commits, no verifiable real-world identity",
            ),
            title="Key Techniques",
            border_style="yellow",
        )
        console.print(techniques)
        console.print()

        console.print(
            Panel(
                "[dim italic]This stage had zero malicious code. Every patch was "
                "legitimate. The attack surface was entirely human trust.[/]",
                border_style="dim",
            )
        )

    # ------------------------------------------------------------------
    # demonstrate
    # ------------------------------------------------------------------
    def demonstrate(self, console: Console) -> None:
        console.print()
        console.print(
            Rule("[bold cyan]Mock Commit History - Trust Progression[/]", style="cyan")
        )
        console.print()

        commits = self._load_commits()
        if not commits:
            console.print("[red]Could not load mock_commits.json[/]")
            return

        table = Table(
            title="Jia Tan Commit Timeline",
            show_header=True,
            header_style="bold white on dark_blue",
            expand=True,
            title_style="bold",
        )
        table.add_column("Date", style="dim", width=12)
        table.add_column("Author", width=16)
        table.add_column("Message", ratio=2)
        table.add_column("Phase", width=16)
        table.add_column("Significance", ratio=2, style="italic")

        for c in commits:
            phase_style = _PHASE_STYLES.get(c["phase"], "white")
            table.add_row(
                c["date"],
                c["author"],
                c["message"],
                f"[{phase_style}]{c['phase']}[/]",
                c.get("note", ""),
            )

        console.print(table)
        console.print()

        # Summary cards
        trust_count = sum(1 for c in commits if c["phase"] == "trust_building")
        inject_count = sum(1 for c in commits if c["phase"] == "injection")
        console.print(
            Columns(
                [
                    Panel(
                        f"[bold cyan]{trust_count}[/] commits",
                        title="Trust Building",
                        border_style="cyan",
                    ),
                    Panel(
                        f"[bold yellow]{inject_count}[/] commits",
                        title="Injection",
                        border_style="yellow",
                    ),
                    Panel(
                        "[bold]~2 years[/] of patience",
                        title="Duration",
                        border_style="magenta",
                    ),
                ],
                equal=True,
                expand=True,
            )
        )

    # ------------------------------------------------------------------
    # indicators / model
    # ------------------------------------------------------------------
    def get_indicators(self) -> list[str]:
        return [
            "New contributor rapidly escalating from docs/tests to build system and core code",
            "Sockpuppet or unknown accounts pressuring maintainers to add committers",
            "Contributor identity not verifiable (no conferences, no employer, VPN-only commits)",
            "Sudden interest in security-sensitive subsystems (CRC, crypto, IFUNC)",
            "Pattern of small benign patches followed by large build-system changes",
        ]

    def get_attack_stage(self) -> AttackStage:
        return AttackStage(
            id=self.id,
            name=self.name,
            order=self.order,
            description=(
                "A multi-year social engineering campaign where the attacker built "
                "trust through legitimate contributions before gaining commit access."
            ),
            technical_detail=(
                "The 'Jia Tan' persona contributed typo fixes and test improvements "
                "starting Jan 2021. Sockpuppet accounts pressured the sole maintainer "
                "to grant commit access. By late 2022, Jia Tan had write access to "
                "the repository and release infrastructure."
            ),
            indicators=self.get_indicators(),
            mitigations=[
                "Require multi-party review for build system changes",
                "Enforce signed commits with verified identities",
                "Rotate maintainers and avoid single points of trust",
                "Monitor contributor scope escalation patterns",
            ],
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_commits() -> list[dict]:
        path = _SAMPLES_DIR / "mock_commits.json"
        if not path.exists():
            return []
        with open(path) as f:
            return json.load(f)
