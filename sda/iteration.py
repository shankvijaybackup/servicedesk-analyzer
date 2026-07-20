"""Baseline versus follow-up comparison for iterative improvement pilots."""

from __future__ import annotations

import hashlib
from importlib import resources

import pandas as pd

from .metrics import compute_metrics, direction
from .normalize import normalize
from .pilots import PilotCharter
from .schema import detect_schema
from .themes import classify


def _prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    schema = detect_schema(df)
    return classify(normalize(df, schema)), schema


def _filter(frame: pd.DataFrame, charter: PilotCharter) -> pd.DataFrame:
    c = charter.cohort
    mask = pd.Series(True, index=frame.index)
    for column, allowed in [
        ("_theme", c.themes), ("assignment_group", c.assignment_groups),
        ("priority", c.priorities), ("application", c.applications),
        ("department", c.departments),
    ]:
        if allowed:
            mask &= frame[column].isin(allowed)
    return frame.loc[mask].copy()


def _fingerprint() -> str:
    rules = resources.files("sda.rules").joinpath("themes.yaml").read_bytes()
    return hashlib.sha256(rules).hexdigest()[:16]


def _change(metric: str, baseline: dict, follow_up: dict) -> dict:
    if baseline["status"] != "measured" or follow_up["status"] != "measured":
        return {"status": "not_measurable", "absolute": None, "improvement_pct": None,
                "reason": "Metric is not measurable in both cohorts."}
    before, after = baseline["value"], follow_up["value"]
    absolute = round(after - before, 2)
    if before == 0:
        return {"status": "partially_measurable", "absolute": absolute,
                "improvement_pct": None,
                "reason": "Percentage change is undefined because the baseline is zero."}
    sign = 1 if direction(metric) == "higher" else -1
    improvement = round(sign * (after - before) / abs(before) * 100, 2)
    return {"status": "measured", "absolute": absolute,
            "improvement_pct": improvement, "reason": None}


def _distribution(frame: pd.DataFrame, column: str) -> dict[str, float]:
    valid = frame[column].dropna()
    if valid.empty:
        return {}
    return {str(k): round(float(v) * 100 / len(valid), 2)
            for k, v in valid.value_counts().items()}


def _mix_distance(left: dict[str, float], right: dict[str, float]) -> float | None:
    if not left or not right:
        return None
    keys = set(left) | set(right)
    return round(sum(abs(left.get(k, 0) - right.get(k, 0)) for k in keys) / 2, 2)


def _comparability(b: pd.DataFrame, f: pd.DataFrame, charter: PilotCharter,
                   overlap_count: int) -> dict:
    checks = []
    blockers = []
    warnings = []
    for label, frame in (("baseline", b), ("follow_up", f)):
        if len(frame) < charter.minimum_cohort_size:
            blockers.append(f"{label} has {len(frame)} tickets; minimum is {charter.minimum_cohort_size}.")
    if overlap_count:
        blockers.append(f"{overlap_count} ticket ids occur in both cohorts.")
    priority_distance = _mix_distance(_distribution(b, "priority"), _distribution(f, "priority"))
    checks.append({"check": "priority_mix_distance_pct", "value": priority_distance})
    if priority_distance is not None and priority_distance > 20:
        warnings.append(f"Priority mix differs by {priority_distance} percentage points.")
    b_cov = b["mttr_hours"].notna().mean() * 100 if len(b) else 0
    f_cov = f["mttr_hours"].notna().mean() * 100 if len(f) else 0
    coverage_delta = round(abs(b_cov - f_cov), 2)
    checks.append({"check": "mttr_coverage_delta_pct", "value": coverage_delta})
    if coverage_delta > 20:
        warnings.append(f"MTTR coverage differs by {coverage_delta} percentage points.")
    status = "insufficient" if blockers else "warning" if warnings else "comparable"
    return {"status": status, "checks": checks, "blockers": blockers, "warnings": warnings}


def _decide(charter: PilotCharter, metrics_b: dict, metrics_f: dict,
            changes: dict, comparability: dict) -> dict:
    if comparability["status"] == "insufficient":
        return {"code": "continue_measuring", "reasons": comparability["blockers"]}

    guardrail_results = []
    required_unavailable = []
    failed = []
    for guardrail in charter.guardrails:
        result = changes[guardrail.metric]
        if result["status"] != "measured":
            status = "not_measurable"
            if guardrail.required:
                required_unavailable.append(guardrail.metric)
        else:
            degradation = max(0.0, -result["improvement_pct"])
            status = "failed" if degradation > guardrail.max_degradation_pct else "passed"
            if status == "failed":
                failed.append(guardrail.metric)
        guardrail_results.append({"metric": guardrail.metric, "status": status,
                                  "limit_pct": guardrail.max_degradation_pct,
                                  "change": result})
    if failed:
        decision = {"code": "stop", "reasons": [f"Required guardrail failed: {m}." for m in failed]}
    elif required_unavailable:
        decision = {"code": "continue_measuring",
                    "reasons": [f"Required guardrail is not measurable: {m}."
                                for m in required_unavailable]}
    else:
        primary = changes[charter.primary_metric]
        if primary["status"] != "measured":
            decision = {"code": "continue_measuring",
                        "reasons": ["The primary metric is not measurable in both cohorts."]}
        elif primary["improvement_pct"] >= charter.minimum_improvement_pct:
            decision = {"code": "widen", "reasons": [
                f"Primary metric improved {primary['improvement_pct']}%, meeting the "
                f"{charter.minimum_improvement_pct}% threshold."]}
        else:
            decision = {"code": "correct", "reasons": [
                f"Primary metric improvement was {primary['improvement_pct']}%, below the "
                f"{charter.minimum_improvement_pct}% threshold."]}
    decision["guardrails"] = guardrail_results
    return decision


def compare_dataframes(baseline_df: pd.DataFrame, follow_up_df: pd.DataFrame,
                       charter: PilotCharter, *, baseline_name: str = "baseline",
                       follow_up_name: str = "follow-up") -> dict:
    """Compare two exports without retaining or returning their raw rows."""
    charter.validate()
    baseline, baseline_schema = _prepare(baseline_df)
    follow_up, follow_up_schema = _prepare(follow_up_df)
    baseline = _filter(baseline, charter)
    follow_up = _filter(follow_up, charter)

    b_ids = set(baseline["ticket_id"].dropna().astype(str))
    f_ids = set(follow_up["ticket_id"].dropna().astype(str))
    overlap = len(b_ids & f_ids)
    metrics_b = compute_metrics(baseline)
    metrics_f = compute_metrics(follow_up)
    compared = set([charter.primary_metric] + [g.metric for g in charter.guardrails])
    changes = {m: _change(m, metrics_b[m], metrics_f[m]) for m in sorted(compared)}
    comparability = _comparability(baseline, follow_up, charter, overlap)
    decision = _decide(charter, metrics_b, metrics_f, changes, comparability)
    return {
        "schema_version": "1.0",
        "method": "observational_before_after",
        "causality_note": "Changes are associations. A before-and-after comparison alone does not prove causation.",
        "rule_pack_fingerprint": _fingerprint(),
        "pilot": charter.to_dict(),
        "baseline": {"source": baseline_name, "cohort_size": len(baseline),
                     "metrics": metrics_b, "fields_detected": baseline_schema["present"]},
        "follow_up": {"source": follow_up_name, "cohort_size": len(follow_up),
                      "metrics": metrics_f, "fields_detected": follow_up_schema["present"]},
        "changes": changes,
        "comparability": comparability,
        "decision": decision,
        "limitations": [
            "Resolution metrics include tickets created in the export window that have valid resolution data.",
            "Ticket mix, staffing, seasonality, and process changes may influence observed differences.",
            "Open backlog rate is not a reliable snapshot metric unless both exports use the same snapshot definition.",
        ],
    }
