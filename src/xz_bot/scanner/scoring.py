"""Risk scoring for scan findings."""
from __future__ import annotations

from xz_bot.common.models import Finding, RiskLevel


def calculate_risk_score(findings: list[Finding]) -> float:
    """Calculate a 0-10 risk score from findings.

    Uses weighted severity scores with cross-category correlation bonus.
    """
    if not findings:
        return 0.0

    # Raw weighted sum
    raw = sum(f.severity.score_weight for f in findings)

    # Cross-category correlation bonus
    categories = {f.category for f in findings}
    if len(categories) >= 3:
        raw *= 1.3  # 30% boost for multi-vector attack patterns
    elif len(categories) >= 2:
        raw *= 1.15

    # Critical finding floor: any CRITICAL finding means at least 6.0
    has_critical = any(f.severity == RiskLevel.CRITICAL for f in findings)

    # Normalize to 0-10 scale (soft cap via logarithmic scaling for many findings)
    import math
    score = min(10.0, 2.0 * math.log2(1 + raw))

    if has_critical:
        score = max(score, 6.0)

    return round(score, 1)
