"""Shared data models for XZ-Bot."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def color(self) -> str:
        return {
            "info": "blue",
            "low": "cyan",
            "medium": "yellow",
            "high": "red",
            "critical": "bold red",
        }[self.value]

    @property
    def score_weight(self) -> float:
        return {"info": 0.5, "low": 2.0, "medium": 4.0, "high": 7.0, "critical": 10.0}[self.value]


@dataclass
class AttackStage:
    id: str
    name: str
    order: int
    description: str
    technical_detail: str
    indicators: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)


@dataclass
class TimelineEvent:
    date: str
    title: str
    description: str
    phase: str  # "trust_building", "injection", "exploitation", "discovery"
    stage_id: Optional[str] = None

    @property
    def phase_color(self) -> str:
        return {
            "trust_building": "blue",
            "injection": "yellow",
            "exploitation": "red",
            "discovery": "green",
        }.get(self.phase, "white")


@dataclass
class Finding:
    rule_id: str
    file_path: str
    line_number: Optional[int]
    severity: RiskLevel
    category: str
    title: str
    description: str
    evidence: str
    recommendation: str


@dataclass
class ScanReport:
    target_path: str
    timestamp: datetime
    findings: list[Finding] = field(default_factory=list)
    agent_reports: dict[str, list[Finding]] = field(default_factory=dict)
    risk_score: float = 0.0

    @property
    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.category] = counts.get(f.category, 0) + 1
        return counts

    @property
    def severity_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.findings:
            key = f.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts
