"""Social engineering detection agent.

Analyzes git history for contributor patterns that match social engineering
campaigns: trust building over time, escalation to build system access,
pressure tactics, and commit velocity anomalies. Falls back to mock data
when git is unavailable.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from xz_bot.common.models import Finding, RiskLevel
from xz_bot.scanner.agent_base import ScanAgent
from xz_bot.scanner.rules.signatures import SOCIAL_ENGINEERING_RULES


class SocialEngAgent(ScanAgent):
    """Agent that detects social engineering patterns in project history."""

    name = "social_engineering"
    category = "social_engineering"

    def scan(self, target_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        target = Path(target_path)

        # Try to load mock commits from samples
        commits = self._load_mock_commits(target)

        # Also try real git history
        if not commits:
            commits = self._load_git_history(target)

        if commits:
            self._analyze_commits(commits, findings)

        # Pattern matching on text files
        self._scan_text_files(target, findings)

        return findings

    def _load_mock_commits(self, target: Path) -> list[dict]:
        """Load mock_commits.json if present in the target."""
        candidates = [
            target / "git_history" / "mock_commits.json",
            target / "mock_commits.json",
        ]
        for path in candidates:
            if path.exists():
                try:
                    return json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
        return []

    def _load_git_history(self, target: Path) -> list[dict]:
        """Try to get real git log from the target directory."""
        git_dir = target if target.is_dir() else target.parent
        try:
            result = subprocess.run(
                [
                    "git", "log", "--format=%H|%an|%ae|%aI|%s",
                    "-n", "200",
                ],
                cwd=str(git_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []
            commits = []
            for line in result.stdout.strip().splitlines():
                parts = line.split("|", 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4],
                    })
            return commits
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return []

    def _analyze_commits(self, commits: list[dict], findings: list[Finding]) -> None:
        """Analyze commit patterns for social engineering indicators."""
        # Group commits by author
        by_author: dict[str, list[dict]] = {}
        for c in commits:
            author = c.get("author", "unknown")
            by_author.setdefault(author, []).append(c)

        for author, author_commits in by_author.items():
            # Check for build system touches by contributors
            build_keywords = {"configure", "makefile", "cmake", "m4", "build", "ci", "workflow"}
            build_touches = [
                c for c in author_commits
                if any(kw in c.get("message", "").lower() for kw in build_keywords)
                or any(
                    kw in str(c.get("files_changed", [])).lower()
                    for kw in build_keywords
                )
            ]

            # Check for trust-building followed by build access
            non_build = len(author_commits) - len(build_touches)
            if build_touches and non_build > 5:
                findings.append(Finding(
                    rule_id="SE-HIST-001",
                    file_path="(git history)",
                    line_number=None,
                    severity=RiskLevel.MEDIUM,
                    category="social_engineering",
                    title=f"Trust-building pattern: {author}",
                    description=(
                        f"Contributor '{author}' made {non_build} non-build commits "
                        f"before touching {len(build_touches)} build system files. "
                        f"This matches the trust-building pattern used in the XZ attack."
                    ),
                    evidence=f"Total commits: {len(author_commits)}, Build touches: {len(build_touches)}",
                    recommendation="Review contributor's build system changes with extra scrutiny.",
                ))

            # Check for pressure language
            pressure_words = {"urgent", "asap", "please merge", "blocking", "need this"}
            for c in author_commits:
                msg = c.get("message", "").lower()
                if any(pw in msg for pw in pressure_words):
                    findings.append(Finding(
                        rule_id="SE-HIST-002",
                        file_path="(git history)",
                        line_number=None,
                        severity=RiskLevel.LOW,
                        category="social_engineering",
                        title=f"Pressure language in commit: {author}",
                        description=(
                            f"Commit message from '{author}' contains pressure language: "
                            f"'{c.get('message', '')[:80]}'"
                        ),
                        evidence=c.get("message", ""),
                        recommendation="Do not rush reviews due to contributor pressure.",
                    ))

            # Check for test fixture additions by the same author who touched build
            test_keywords = {"test", "fixture", "data", "sample"}
            test_touches = [
                c for c in author_commits
                if any(kw in c.get("message", "").lower() for kw in test_keywords)
            ]
            if build_touches and test_touches:
                findings.append(Finding(
                    rule_id="SE-HIST-003",
                    file_path="(git history)",
                    line_number=None,
                    severity=RiskLevel.HIGH,
                    category="social_engineering",
                    title=f"Build + test fixture pattern: {author}",
                    description=(
                        f"Contributor '{author}' modified both build system files "
                        f"and test fixtures. In the XZ attack, the attacker added "
                        f"obfuscated payloads as test data and modified the build "
                        f"to extract them."
                    ),
                    evidence=(
                        f"Build commits: {len(build_touches)}, "
                        f"Test commits: {len(test_touches)}"
                    ),
                    recommendation=(
                        "Cross-reference test fixture additions with build changes. "
                        "Verify test data is not consumed by build scripts."
                    ),
                ))

    def _scan_text_files(self, target: Path, findings: list[Finding]) -> None:
        """Apply text-based social engineering pattern rules."""
        import fnmatch

        if target.is_file():
            files = [target]
        else:
            files = [p for p in target.rglob("*") if p.is_file()]

        for fpath in files:
            if fpath.suffix.lower() not in {".json", ".md", ".txt"}:
                continue
            try:
                text = fpath.read_text(errors="replace")
            except (OSError, PermissionError):
                continue

            for rule in SOCIAL_ENGINEERING_RULES:
                if not any(fnmatch.fnmatch(fpath.name, g) for g in rule.file_globs):
                    continue
                for line_no, line in enumerate(text.splitlines(), start=1):
                    match = rule.pattern.search(line)
                    if match:
                        lines = text.splitlines()
                        start = max(0, line_no - 2)
                        end = min(len(lines), line_no + 2)
                        evidence = "\n".join(lines[start:end])
                        findings.append(Finding(
                            rule_id=rule.id,
                            file_path=str(fpath),
                            line_number=line_no,
                            severity=rule.severity,
                            category=rule.category,
                            title=rule.name,
                            description=rule.description,
                            evidence=evidence,
                            recommendation=rule.recommendation,
                        ))
