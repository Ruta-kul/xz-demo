"""CLI entry point for XZ-Bot."""
from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console

console = Console()

BANNER = r"""
 __  ______    ____        _
 \ \/ /__  /  | __ )  ___ | |_
  \  /  / /   |  _ \ / _ \| __|
  /  \ / /_   | |_) | (_) | |_
 /_/\_\/____|  |____/ \___/ \__|

  CVE-2024-3094 Interactive Lab
  Agentic AI Vulnerability Scanner
"""


@click.group()
@click.version_option(version="1.0.0", prog_name="xz-bot")
def main():
    """XZ-Bot: Interactive XZ Backdoor Demo & Agentic AI Vulnerability Scanner."""
    pass


@main.command()
@click.option("--stage", "-s", type=str, default=None, help="Run a specific stage (1-5 or stage id)")
@click.option("--list-stages", "-l", is_flag=True, help="List all available stages")
@click.option("--timeline", "-t", is_flag=True, help="Show the attack timeline")
def simulate(stage, list_stages, timeline):
    """Replay the XZ backdoor attack step by step."""
    from xz_bot.simulator.engine import SimulatorEngine

    engine = SimulatorEngine()

    if list_stages:
        engine.list_stages()
        return

    if timeline:
        engine.print_timeline()
        return

    if stage:
        engine.run_stage(stage)
    else:
        engine.run_all()


@main.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--samples", is_flag=True, help="Scan the bundled samples directory")
def scan(path, output_format, samples):
    """Run the agentic AI vulnerability scanner on a target path."""
    from xz_bot.scanner.orchestrator import ScanOrchestrator
    from xz_bot.scanner.report import format_rich_report, format_json_report

    if samples:
        path = str(Path(__file__).resolve().parents[1] / "samples")
        if not Path(path).exists():
            path = str(Path(__file__).resolve().parents[2] / "samples")

    console.print(f"\n[bold cyan]Scanning:[/] {path}\n")

    orchestrator = ScanOrchestrator()

    def progress(agent: str, status: str):
        console.print(f"  [dim]Agent[/] [bold cyan]{agent}[/]: {status}")

    report = orchestrator.scan(path, progress_callback=progress)

    if output_format == "json":
        click.echo(json.dumps(format_json_report(report), indent=2))
    else:
        format_rich_report(report, console)


@main.command()
def tui():
    """Launch the interactive terminal UI."""
    from xz_bot.tui.app import run_tui
    run_tui()


@main.command()
@click.option("--port", "-p", default=5000, help="Port to run the web server on")
@click.option("--debug", is_flag=True, help="Enable Flask debug mode")
def web(port, debug):
    """Launch the web dashboard."""
    from xz_bot.web.app import run_web
    console.print(f"\n[bold cyan]Starting XZ-Bot Web Dashboard[/]")
    console.print(f"[dim]Open http://localhost:{port} in your browser[/]\n")
    run_web(port=port, debug=debug)


@main.command()
def demo():
    """Run a quick demo: simulate all stages, then scan samples."""
    from rich.rule import Rule

    console.print(BANNER, style="bold cyan")

    # Run simulation
    console.print(Rule("[bold]Phase 1: Attack Simulation[/]", style="blue"))
    from xz_bot.simulator.engine import SimulatorEngine
    engine = SimulatorEngine()
    engine.run_all()

    # Run scanner
    console.print()
    console.print(Rule("[bold]Phase 2: Agentic AI Scanner[/]", style="blue"))
    from xz_bot.scanner.orchestrator import ScanOrchestrator
    from xz_bot.scanner.report import format_rich_report

    samples_path = str(Path(__file__).resolve().parents[1] / "samples")
    if not Path(samples_path).exists():
        samples_path = str(Path(__file__).resolve().parents[2] / "samples")

    orchestrator = ScanOrchestrator()

    def progress(agent: str, status: str):
        console.print(f"  [dim]Agent[/] [bold cyan]{agent}[/]: {status}")

    report = orchestrator.scan(samples_path, progress_callback=progress)
    format_rich_report(report, console)

    # Timeline
    console.print()
    console.print(Rule("[bold]Phase 3: Attack Timeline[/]", style="blue"))
    engine.print_timeline()


if __name__ == "__main__":
    main()
