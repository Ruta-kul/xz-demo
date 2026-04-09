"""Scanner screen - live vulnerability scanning interface."""
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, Input, Button, RichLog, DataTable
from textual.containers import Horizontal, Vertical
from textual.worker import Worker, WorkerState
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from xz_bot.scanner.orchestrator import ScanOrchestrator
from xz_bot.common.models import ScanReport
from xz_bot.tui.widgets.risk_gauge import RiskGauge


class ScannerScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back to Menu"),
    ]

    def __init__(self):
        super().__init__()
        self.orchestrator = ScanOrchestrator()
        self.current_report: ScanReport | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="scanner-layout"):
            yield Static(
                Panel(
                    "[bold cyan]Agentic AI Vulnerability Scanner[/]\n"
                    "Multi-agent autonomous analysis for supply chain backdoor patterns",
                    border_style="cyan",
                ),
                id="scanner-title",
            )
            with Horizontal(id="scan-controls"):
                yield Input(
                    placeholder="Enter path to scan (e.g., ./samples)",
                    id="scan-path",
                )
                yield Button("Scan", variant="primary", id="scan-btn")
                yield Button("Scan Samples", variant="success", id="scan-samples-btn")
            yield RiskGauge(score=0.0)
            yield RichLog(highlight=True, markup=True, id="scan-log", wrap=True)
            yield DataTable(id="findings-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#findings-table", DataTable)
        table.add_columns("Sev", "Rule", "Category", "Title", "File", "Line")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan-btn":
            path = self.query_one("#scan-path", Input).value.strip()
            if path:
                self._start_scan(path)
        elif event.button.id == "scan-samples-btn":
            samples_path = str(Path(__file__).resolve().parents[3] / "samples")
            self.query_one("#scan-path", Input).value = samples_path
            self._start_scan(samples_path)

    def _start_scan(self, path: str) -> None:
        log = self.query_one("#scan-log", RichLog)
        log.clear()
        table = self.query_one("#findings-table", DataTable)
        table.clear()
        self.query_one(RiskGauge).update_score(0.0)
        log.write(Panel(f"[bold]Scanning: [cyan]{path}[/cyan][/]", border_style="yellow"))
        self.run_worker(self._do_scan(path), name="scanner", thread=True)

    async def _do_scan(self, path: str) -> ScanReport:
        log = self.query_one("#scan-log", RichLog)

        def progress(agent_name: str, status: str):
            log.write(f"  [dim]Agent[/] [bold cyan]{agent_name}[/]: {status}")

        report = self.orchestrator.scan(path, progress_callback=progress)
        self.current_report = report
        return report

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name == "scanner" and event.state == WorkerState.SUCCESS:
            report = event.worker.result
            if report:
                self._display_results(report)

    def _display_results(self, report: ScanReport) -> None:
        log = self.query_one("#scan-log", RichLog)
        gauge = self.query_one(RiskGauge)
        table = self.query_one("#findings-table", DataTable)

        gauge.update_score(report.risk_score)

        log.write("")
        log.write(Panel(
            f"[bold]Scan Complete[/]\n"
            f"  Findings: [bold]{len(report.findings)}[/]\n"
            f"  Risk Score: [bold]{report.risk_score:.1f}/10[/]\n"
            f"  Categories: {report.summary}",
            border_style="green",
        ))

        for agent_name, findings in report.agent_reports.items():
            log.write(f"  [bold]{agent_name}[/]: {len(findings)} findings")

        for f in sorted(report.findings, key=lambda x: x.severity.score_weight, reverse=True):
            sev_text = Text(f.severity.value.upper(), style=f.severity.color)
            table.add_row(
                sev_text,
                f.rule_id,
                f.category,
                f.title,
                str(Path(f.file_path).name) if f.file_path else "-",
                str(f.line_number) if f.line_number else "-",
            )

    def action_go_back(self) -> None:
        self.app.switch_mode("welcome")
