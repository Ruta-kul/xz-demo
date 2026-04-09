"""Supply-chain analysis agent.

Walks build system files (Makefile*, configure*, CMakeLists.txt, *.m4,
CI workflow files, Dockerfiles) and applies supply-chain pattern rules.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from xz_bot.common.models import Finding, RiskLevel
from xz_bot.scanner.agent_base import ScanAgent
from xz_bot.scanner.rules.signatures import SUPPLY_CHAIN_RULES, PatternRule


# Build-related file globs that this agent considers
_BUILD_GLOBS: list[str] = [
    "Makefile",
    "Makefile.*",
    "*.am",
    "*.mk",
    "*.m4",
    "configure",
    "configure.*",
    "*.ac",
    "CMakeLists.txt",
    "*.cmake",
    "*.sh",
    "Dockerfile",
    "Dockerfile.*",
    "*.yml",
    "*.yaml",
    "meson.build",
    "build.gradle",
    "build.gradle.kts",
]


def _matches_any_glob(filename: str, globs: list[str]) -> bool:
    """Return True if *filename* matches at least one glob pattern."""
    return any(fnmatch.fnmatch(filename, g) for g in globs)


def _is_build_file(path: Path) -> bool:
    """Check whether *path* looks like a build-system file."""
    name = path.name
    if _matches_any_glob(name, _BUILD_GLOBS):
        return True
    # Also pick up CI workflow directories
    parts = path.parts
    if ".github" in parts or ".gitlab-ci" in parts:
        return True
    return False


class SupplyChainAgent(ScanAgent):
    """Agent that detects supply-chain compromise patterns in build files."""

    name = "supply_chain"
    category = "supply_chain"

    def scan(self, target_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        target = Path(target_path)

        for fpath in self._walk_build_files(target):
            try:
                text = fpath.read_text(errors="replace")
            except (OSError, PermissionError):
                continue

            for rule in SUPPLY_CHAIN_RULES:
                if not _matches_any_glob(fpath.name, rule.file_globs):
                    continue
                self._apply_rule(rule, fpath, text, findings)

        return findings

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _walk_build_files(root: Path):
        """Yield all build-related files under *root*."""
        if root.is_file():
            if _is_build_file(root):
                yield root
            return

        for path in root.rglob("*"):
            if path.is_file() and _is_build_file(path):
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
                # Gather a few lines of context around the match
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
