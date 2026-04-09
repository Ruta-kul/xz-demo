"""Abstract base class for all scan agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from xz_bot.common.models import Finding


class ScanAgent(ABC):
    """Base class that every scanner agent must implement.

    Each agent is responsible for a single category of analysis (supply chain,
    backdoor patterns, obfuscation, social engineering).  The orchestrator
    drives two passes:

    1. ``scan()`` -- independent analysis of the target path.
    2. ``cross_reference()`` -- optional second pass that can inspect
       findings produced by *other* agents and emit additional findings
       (e.g. correlation between build injection + obfuscation).
    """

    name: str = "base"
    category: str = "general"

    @abstractmethod
    def scan(self, target_path: Path) -> list[Finding]:
        """Scan *target_path* and return a list of findings."""
        ...

    def cross_reference(
        self,
        own: list[Finding],
        others: dict[str, list[Finding]],
    ) -> list[Finding]:
        """Optional second pass that correlates findings across agents.

        Parameters
        ----------
        own:
            Findings this agent produced in Pass 1.
        others:
            Mapping of ``agent.name -> findings`` for all *other* agents.

        Returns an (possibly empty) list of new correlation findings.
        """
        return []
