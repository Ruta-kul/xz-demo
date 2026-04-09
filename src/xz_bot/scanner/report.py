"""Scan report formatting for terminal and JSON output."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from xz_bot.common.models import ScanReport


def format_rich_report(report: ScanReport, console: Console) -> None:
    """Render a ScanReport as Rich tables and panels."""
    # Header
    console.print()
    risk_color = _risk_color(report.risk_score)
    console.print(Panel(
        Text.assemble(
            ("Scan Results\n\n", "bold"),
            ("Target: ", "dim"),
            (f"{report.target_path}\n", ""),
            ("Time: ", "dim"),
            (f"{report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n", ""),
            ("Findings: ", "dim"),
            (f"{len(report.findings)}\n", "bold"),
            ("Risk Score: ", "dim"),
            (f"{report.risk_score:.1f}/10", f"bold {risk_color}"),
        ),
        title="[bold]Agentic AI Vulnerability Scanner[/]",
        border_style=risk_color,
    ))

    # Agent summary
    if report.agent_reports:
        console.print()
        agent_text = Text()
        for name, findings in report.agent_reports.items():
            agent_text.append(f"  {name}: ", style="bold cyan")
            agent_text.append(f"{len(findings)} findings\n")
        console.print(Panel(agent_text, title="Agent Reports", border_style="cyan"))

    # Findings table
    if report.findings:
        console.print()
        table = Table(
            title="Findings",
            show_header=True,
            header_style="bold white on dark_blue",
            expand=True,
        )
        table.add_column("Sev", width=10)
        table.add_column("Rule", width=14)
        table.add_column("Category", width=18)
        table.add_column("Title", ratio=2)
        table.add_column("File", ratio=1)
        table.add_column("Line", width=6)

        for f in sorted(report.findings, key=lambda x: x.severity.score_weight, reverse=True):
            sev_text = Text(f.severity.value.upper(), style=f.severity.color)
            fname = f.file_path.split("/")[-1] if f.file_path else "-"
            table.add_row(
                sev_text,
                f.rule_id,
                f.category,
                f.title,
                fname,
                str(f.line_number) if f.line_number else "-",
            )

        console.print(table)
    else:
        console.print("\n[green]No findings. Target appears clean.[/]\n")


def format_json_report(report: ScanReport) -> dict:
    """Convert ScanReport to a JSON-serializable dict."""
    return {
        "target_path": report.target_path,
        "timestamp": report.timestamp.isoformat(),
        "risk_score": report.risk_score,
        "total_findings": len(report.findings),
        "summary": report.summary,
        "severity_counts": report.severity_counts,
        "findings": [
            {
                "rule_id": f.rule_id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "severity": f.severity.value,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "evidence": f.evidence[:200],
                "recommendation": f.recommendation,
            }
            for f in report.findings
        ],
        "agent_reports": {
            name: len(findings) for name, findings in report.agent_reports.items()
        },
    }


def _risk_color(score: float) -> str:
    if score <= 3.0:
        return "green"
    elif score <= 6.0:
        return "yellow"
    elif score <= 8.0:
        return "red"
    return "bold red"
