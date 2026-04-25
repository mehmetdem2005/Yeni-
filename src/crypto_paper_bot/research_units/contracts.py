from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class ReviewDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"


@dataclass(frozen=True)
class ResearchTask:
    name: str
    objective: str
    inputs: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResearchReport:
    task_name: str
    decision: ReviewDecision
    summary: str
    metrics: dict[str, Any] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)


class ResearchUnit(Protocol):
    name: str

    def run(self, task: ResearchTask) -> ResearchReport:
        ...


@dataclass
class RiskAuditUnit:
    name: str = "risk_auditor"

    def run(self, task: ResearchTask) -> ResearchReport:
        metrics = task.inputs.get("metrics", {})
        risks: list[str] = []
        if metrics.get("max_drawdown", 0.0) < -0.15:
            risks.append("max_drawdown_breach")
        if metrics.get("portfolio_risk", 0.0) > 0.01:
            risks.append("portfolio_risk_breach")
        decision = ReviewDecision.REJECT if risks else ReviewDecision.APPROVE
        return ResearchReport(
            task_name=task.name,
            decision=decision,
            summary="Risk audit completed.",
            metrics=metrics,
            risks=risks,
        )
