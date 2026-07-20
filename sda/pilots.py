"""Pilot definitions for iterative service-desk improvement.

These objects contain configuration only. They never contain source ticket rows.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


SUPPORTED_METRICS = {
    "median_mttr_hours",
    "p90_mttr_hours",
    "open_backlog_rate",
    "reopen_rate",
    "first_contact_resolution_rate",
    "sla_breach_rate",
    "escalation_rate",
    "ai_acceptance_rate",
    "human_override_rate",
    "confirmed_resolution_rate",
}


@dataclass(frozen=True)
class CohortSpec:
    themes: tuple[str, ...] = ()
    assignment_groups: tuple[str, ...] = ()
    priorities: tuple[str, ...] = ()
    applications: tuple[str, ...] = ()
    departments: tuple[str, ...] = ()


@dataclass(frozen=True)
class Guardrail:
    metric: str
    max_degradation_pct: float = 0.0
    required: bool = True

    def validate(self) -> None:
        if self.metric not in SUPPORTED_METRICS:
            raise ValueError(f"Unsupported guardrail metric: {self.metric}")
        if self.max_degradation_pct < 0:
            raise ValueError("Guardrail degradation limit cannot be negative.")


@dataclass(frozen=True)
class PilotCharter:
    pilot_id: str
    name: str
    intervention: str
    cohort: CohortSpec = field(default_factory=CohortSpec)
    primary_metric: str = "median_mttr_hours"
    minimum_improvement_pct: float = 10.0
    guardrails: tuple[Guardrail, ...] = ()
    owner: str | None = None
    human_approval_required: bool = True
    rollback_condition: str = "Stop if a required guardrail exceeds its limit."
    minimum_cohort_size: int = 20

    def validate(self) -> None:
        if not self.pilot_id.strip() or not self.name.strip() or not self.intervention.strip():
            raise ValueError("Pilot id, name, and intervention are required.")
        if self.primary_metric not in SUPPORTED_METRICS:
            raise ValueError(f"Unsupported primary metric: {self.primary_metric}")
        if self.minimum_improvement_pct < 0:
            raise ValueError("Minimum improvement cannot be negative.")
        if self.minimum_cohort_size < 1:
            raise ValueError("Minimum cohort size must be at least one.")
        for guardrail in self.guardrails:
            guardrail.validate()

    def to_dict(self) -> dict:
        return asdict(self)


def recommend_pilot(analysis: dict) -> dict | None:
    """Return one transparent, deterministic pilot recommendation."""
    backlog = analysis.get("opportunities", {}).get("backlog", [])
    if not backlog:
        return None
    confidence_weight = {"High": 1.0, "Medium": 0.65, "Low": 0.25}
    complexity_weight = {"Low": 1.0, "Medium": 0.7, "High": 0.35}
    risk_weight = {"Low": 1.0, "Medium": 0.7, "High": 0.25}
    scored = []
    for item in backlog:
        components = {
            "volume_share": float(item.get("pct_of_total", 0)) / 100.0,
            "confidence": confidence_weight.get(item.get("confidence"), 0.25),
            "feasibility": complexity_weight.get(item.get("implementation_complexity"), 0.35),
            "safety": risk_weight.get(item.get("risk_level"), 0.25),
        }
        score = 1.0
        for value in components.values():
            score *= value
        scored.append((score, item, components))
    score, item, components = max(scored, key=lambda row: row[0])
    return {
        "theme": item["theme"],
        "intervention_type": item["primary_type"],
        "score": round(score * 100, 2),
        "score_components": {k: round(v * 100, 2) for k, v in components.items()},
        "addressable_tickets": item["tickets_addressable"],
        "confidence": item["confidence"],
        "risk": item["risk_level"],
        "reason": "Highest combined volume, evidence confidence, feasibility, and safety score.",
    }
