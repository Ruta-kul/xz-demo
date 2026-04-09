"""Base class for XZ backdoor simulation stages."""

from abc import ABC, abstractmethod

from rich.console import Console

from xz_bot.common.models import AttackStage


class Stage(ABC):
    """Abstract base class for a single stage of the XZ backdoor attack."""

    id: str
    name: str
    order: int

    @abstractmethod
    def explain(self, console: Console) -> None:
        """Display a detailed educational explanation of this attack stage."""
        ...

    @abstractmethod
    def demonstrate(self, console: Console) -> None:
        """Show concrete artifacts, code, or data illustrating this stage."""
        ...

    @abstractmethod
    def get_indicators(self) -> list[str]:
        """Return indicators of compromise / suspicious patterns for this stage."""
        ...

    @abstractmethod
    def get_attack_stage(self) -> AttackStage:
        """Return the structured AttackStage model for this stage."""
        ...
