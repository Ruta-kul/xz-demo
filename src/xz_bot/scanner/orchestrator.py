"""Scan orchestrator - coordinates multi-agent vulnerability scanning."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from xz_bot.common.models import ScanReport
from xz_bot.scanner.agent_base import ScanAgent
from xz_bot.scanner.agents.backdoor import BackdoorAgent
from xz_bot.scanner.agents.obfuscation import ObfuscationAgent
from xz_bot.scanner.agents.social_eng import SocialEngAgent
from xz_bot.scanner.agents.supply_chain import SupplyChainAgent
from xz_bot.scanner.scoring import calculate_risk_score


class ScanOrchestrator:
    """Multi-pass scan coordinator.

    Pass 1: Each agent scans independently.
    Pass 2: Agents cross-reference findings from other agents.
    Pass 3: Deduplicate, score, and consolidate into a ScanReport.
    """

    def __init__(self) -> None:
        self.agents: list[ScanAgent] = [
            SupplyChainAgent(),
            BackdoorAgent(),
            ObfuscationAgent(),
            SocialEngAgent(),
        ]

    def scan(
        self,
        target_path: str,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> ScanReport:
        target = Path(target_path)
        agent_findings: dict[str, list] = {}

        # Pass 1: Independent scans
        for agent in self.agents:
            if progress_callback:
                progress_callback(agent.name, "scanning...")
            findings = agent.scan(target)
            agent_findings[agent.name] = findings
            if progress_callback:
                progress_callback(agent.name, f"found {len(findings)} issues")

        # Pass 2: Cross-reference
        if progress_callback:
            progress_callback("orchestrator", "cross-referencing findings...")

        for agent in self.agents:
            others = {
                name: f for name, f in agent_findings.items()
                if name != agent.name
            }
            cross_findings = agent.cross_reference(
                agent_findings[agent.name], others
            )
            if cross_findings:
                agent_findings[agent.name].extend(cross_findings)
                if progress_callback:
                    progress_callback(agent.name, f"+{len(cross_findings)} cross-ref findings")

        # Pass 3: Consolidate and score
        all_findings = []
        for findings in agent_findings.values():
            all_findings.extend(findings)

        # Deduplicate by (rule_id, file_path, line_number)
        seen = set()
        unique = []
        for f in all_findings:
            key = (f.rule_id, f.file_path, f.line_number)
            if key not in seen:
                seen.add(key)
                unique.append(f)

        risk_score = calculate_risk_score(unique)

        if progress_callback:
            progress_callback("orchestrator", f"complete - risk score: {risk_score:.1f}/10")

        return ScanReport(
            target_path=str(target),
            timestamp=datetime.now(),
            findings=unique,
            agent_reports=agent_findings,
            risk_score=risk_score,
        )
