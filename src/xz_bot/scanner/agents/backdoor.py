"""Backdoor detection agent.

Scans C/C++ source files for patterns associated with binary backdoors:
IFUNC resolvers, symbol interposition, GOT/PLT manipulation, suspicious
crypto function usage, and embedded binary blobs.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from xz_bot.common.models import Finding, RiskLevel
from xz_bot.scanner.agent_base import ScanAgent
from xz_bot.scanner.rules.signatures import BACKDOOR_RULES, PatternRule

_SOURCE_GLOBS: list[str] = [
    "*.c",
    "*.h",
    "*.cpp",
    "*.cc",
    "*.cxx",
    "*.S",
    "*.s",
    "*.ld",
]


def _matches_any_glob(filename: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(filename, g) for g in globs)


def _is_source_file(path: Path) -> bool:
    return _matches_any_glob(path.name, _SOURCE_GLOBS)


class BackdoorAgent(ScanAgent):
    """Agent that detects backdoor insertion patterns in C/C++ source."""

    name = "backdoor"
    category = "backdoor"

    def scan(self, target_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        target = Path(target_path)

        for fpath in self._walk_sources(target):
            try:
                text = fpath.read_text(errors="replace")
            except (OSError, PermissionError):
                continue

            for rule in BACKDOOR_RULES:
                if not _matches_any_glob(fpath.name, rule.file_globs):
                    continue
                self._apply_rule(rule, fpath, text, findings)

        return findings

    def cross_reference(
        self,
        own: list[Finding],
        others: dict[str, list[Finding]],
    ) -> list[Finding]:
        """Boost severity when IFUNC + crypto function references co-occur."""
        cross_findings: list[Finding] = []

        has_ifunc = any(f.rule_id == "BD-001" for f in own)
        has_crypto = any(f.rule_id == "BD-004" for f in own)

        if has_ifunc and has_crypto:
            cross_findings.append(
                Finding(
                    rule_id="BD-XREF-001",
                    file_path="(cross-reference)",
                    line_number=None,
                    severity=RiskLevel.CRITICAL,
                    category="backdoor",
                    title="IFUNC + crypto function correlation",
                    description=(
                        "Both IFUNC resolver usage and RSA_public_decrypt "
                        "references were found. This is the exact attack "
                        "pattern used in the XZ backdoor to intercept SSH "
                        "authentication."
                    ),
                    evidence=(
                        "IFUNC resolver (BD-001) combined with "
                        "RSA_public_decrypt reference (BD-004)"
                    ),
                    recommendation=(
                        "URGENT: Investigate the relationship between IFUNC "
                        "resolvers and crypto function usage immediately."
                    ),
                )
            )

        # Also flag if backdoor patterns appear alongside supply-chain injection
        supply_findings = others.get("supply_chain", [])
        if own and supply_findings:
            # If we have any backdoor findings AND there are supply-chain
            # injection findings, flag the correlation
            bd_high = [f for f in own if f.severity in (RiskLevel.CRITICAL, RiskLevel.HIGH)]
            sc_high = [f for f in supply_findings if f.severity in (RiskLevel.CRITICAL, RiskLevel.HIGH)]
            if bd_high and sc_high:
                cross_findings.append(
                    Finding(
                        rule_id="BD-XREF-002",
                        file_path="(cross-reference)",
                        line_number=None,
                        severity=RiskLevel.CRITICAL,
                        category="backdoor",
                        title="Backdoor code + build injection correlation",
                        description=(
                            "High-severity backdoor patterns were found "
                            "alongside supply-chain build injection. This "
                            "combination strongly suggests a coordinated "
                            "attack similar to the XZ Utils compromise."
                        ),
                        evidence=(
                            f"{len(bd_high)} backdoor finding(s) + "
                            f"{len(sc_high)} supply-chain finding(s)"
                        ),
                        recommendation=(
                            "URGENT: Treat this as a potential active compromise. "
                            "Audit all recent build system and source changes."
                        ),
                    )
                )

        return cross_findings

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _walk_sources(root: Path):
        if root.is_file():
            if _is_source_file(root):
                yield root
            return
        for path in root.rglob("*"):
            if path.is_file() and _is_source_file(path):
                yield path

    @staticmethod
    def _apply_rule(
        rule: PatternRule,
        fpath: Path,
        text: str,
        findings: list[Finding],
    ) -> None:
        for line_no, line in enumerate(text.splitlines(), start=1):
            match = rule.pattern.search(line)
            if match:
                lines = text.splitlines()
                start = max(0, line_no - 3)
                end = min(len(lines), line_no + 2)
                evidence = "\n".join(lines[start:end])

                findings.append(
                    Finding(
                        rule_id=rule.id,
                        file_path=str(fpath),
                        line_number=line_no,
                        severity=rule.severity,
                        category=rule.category,
                        title=rule.name,
                        description=rule.description,
                        evidence=evidence,
                        recommendation=rule.recommendation,
                    )
                )
