"""Obfuscation detection agent.

Inspects all files for obfuscation patterns: high-entropy data, multi-stage
pipelines (tr/head/tail), base64 decoding, compressed archive extraction,
hex-encoded strings, and deliberately confusing variable names.
"""
from __future__ import annotations

import fnmatch
import math
from collections import Counter
from pathlib import Path

from xz_bot.common.models import Finding, RiskLevel
from xz_bot.scanner.agent_base import ScanAgent
from xz_bot.scanner.rules.signatures import OBFUSCATION_RULES, PatternRule

# Skip binary-heavy extensions where entropy checks don't apply
_SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz", ".bz2",
    ".xz", ".7z", ".pyc", ".pyo", ".so", ".dylib", ".dll",
}


def _matches_any_glob(filename: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(filename, g) for g in globs)


def _shannon_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of raw bytes (0-8 bits)."""
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum(
        (c / length) * math.log2(c / length)
        for c in counts.values()
        if c > 0
    )


class ObfuscationAgent(ScanAgent):
    """Agent that detects obfuscation and hidden payload patterns."""

    name = "obfuscation"
    category = "obfuscation"

    def scan(self, target_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        target = Path(target_path)

        if target.is_file():
            self._check_file(target, findings)
        else:
            for path in target.rglob("*"):
                if path.is_file():
                    self._check_file(path, findings)

        return findings

    def cross_reference(
        self,
        own: list[Finding],
        others: dict[str, list[Finding]],
    ) -> list[Finding]:
        """If obfuscated data + build injection, flag as critical."""
        cross: list[Finding] = []
        supply = others.get("supply_chain", [])
        if own and supply:
            ob_high = [f for f in own if f.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
            sc_high = [f for f in supply if f.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
            if ob_high and sc_high:
                cross.append(Finding(
                    rule_id="OB-XREF-001",
                    file_path="(cross-reference)",
                    line_number=None,
                    severity=RiskLevel.CRITICAL,
                    category="obfuscation",
                    title="Obfuscated data + build injection correlation",
                    description=(
                        "High-severity obfuscation patterns were found alongside "
                        "supply-chain build injection. This matches the XZ attack "
                        "pattern where obfuscated payloads were extracted by "
                        "weaponized build scripts."
                    ),
                    evidence=(
                        f"{len(ob_high)} obfuscation finding(s) + "
                        f"{len(sc_high)} supply-chain finding(s)"
                    ),
                    recommendation=(
                        "URGENT: Audit all obfuscated data referenced by build "
                        "scripts. Decompress and inspect all test fixtures."
                    ),
                ))
        return cross

    def _check_file(self, path: Path, findings: list[Finding]) -> None:
        if path.suffix.lower() in _SKIP_EXTENSIONS:
            return

        try:
            raw = path.read_bytes()
        except (OSError, PermissionError):
            return

        # Entropy check for non-trivial files
        if len(raw) > 256:
            entropy = _shannon_entropy(raw)
            if entropy > 7.2:
                findings.append(Finding(
                    rule_id="OB-ENT-001",
                    file_path=str(path),
                    line_number=None,
                    severity=RiskLevel.MEDIUM,
                    category="obfuscation",
                    title="High-entropy file detected",
                    description=(
                        f"File has Shannon entropy of {entropy:.2f} bits/byte "
                        f"(threshold: 7.2). May contain compressed or encrypted data."
                    ),
                    evidence=f"Entropy: {entropy:.2f}/8.0, Size: {len(raw)} bytes",
                    recommendation="Inspect file contents; verify it is not an obfuscated payload.",
                ))

        # Text-based pattern matching
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            return

        for rule in OBFUSCATION_RULES:
            if not _matches_any_glob(path.name, rule.file_globs):
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = rule.pattern.search(line)
                if match:
                    lines = text.splitlines()
                    start = max(0, line_no - 3)
                    end = min(len(lines), line_no + 2)
                    evidence = "\n".join(lines[start:end])
                    findings.append(Finding(
                        rule_id=rule.id,
                        file_path=str(path),
                        line_number=line_no,
                        severity=rule.severity,
                        category=rule.category,
                        title=rule.name,
                        description=rule.description,
                        evidence=evidence,
                        recommendation=rule.recommendation,
                    ))
