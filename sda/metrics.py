"""Outcome metrics with explicit availability and denominators."""

from __future__ import annotations

import pandas as pd

from . import util


LOWER_IS_BETTER = {
    "median_mttr_hours", "p90_mttr_hours", "open_backlog_rate", "reopen_rate",
    "sla_breach_rate", "escalation_rate", "human_override_rate",
}
HIGHER_IS_BETTER = {
    "first_contact_resolution_rate", "ai_acceptance_rate", "confirmed_resolution_rate",
}


def _unavailable(reason: str) -> dict:
    return {"status": "not_measurable", "value": None, "numerator": None,
            "denominator": 0, "coverage_pct": 0.0, "reason": reason}


def _numeric_metric(series: pd.Series, name: str, total: int) -> dict:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if valid.empty:
        return _unavailable(f"{name} has no valid values.")
    value = valid.median() if name == "median_mttr_hours" else valid.quantile(0.9)
    return {"status": "measured", "value": util.safe_round(value), "numerator": None,
            "denominator": int(len(valid)), "coverage_pct": util.pct(len(valid), total),
            "reason": None}


def _rate(series: pd.Series, total: int, label: str) -> dict:
    valid = series.dropna()
    if valid.empty:
        return _unavailable(f"{label} is missing or has no valid values.")
    truth = int((valid == True).sum())  # noqa: E712
    return {"status": "measured", "value": util.pct(truth, len(valid)),
            "numerator": truth, "denominator": int(len(valid)),
            "coverage_pct": util.pct(len(valid), total), "reason": None}


def compute_metrics(classified: pd.DataFrame) -> dict:
    total = len(classified)
    out = {
        "ticket_count": {"status": "measured", "value": total, "numerator": total,
                         "denominator": total, "coverage_pct": 100.0 if total else 0.0,
                         "reason": None}
    }
    mttr = classified.get("mttr_hours", pd.Series(dtype=float))
    out["median_mttr_hours"] = _numeric_metric(mttr, "median_mttr_hours", total)
    out["p90_mttr_hours"] = _numeric_metric(mttr, "p90_mttr_hours", total)

    status = classified.get("status", pd.Series(dtype="object")).dropna()
    if status.empty:
        out["open_backlog_rate"] = _unavailable("Status is missing or has no valid values.")
    else:
        open_count = int((~status.isin(["Resolved", "Cancelled"])).sum())
        out["open_backlog_rate"] = {
            "status": "measured", "value": util.pct(open_count, len(status)),
            "numerator": open_count, "denominator": int(len(status)),
            "coverage_pct": util.pct(len(status), total),
            "reason": "A ticket export is not necessarily a point-in-time backlog snapshot.",
        }

    boolean_metrics = {
        "first_contact_resolution_rate": "first_contact_resolved",
        "sla_breach_rate": "sla_breached",
        "escalation_rate": "escalated",
        "ai_acceptance_rate": "ai_accepted",
        "human_override_rate": "human_override",
        "confirmed_resolution_rate": "user_confirmed_resolved",
    }
    for metric, column in boolean_metrics.items():
        series = classified.get(column)
        out[metric] = (_rate(series, total, column) if series is not None
                       else _unavailable(f"{column} was not detected."))

    reopen = classified.get("reopen_count")
    if reopen is None:
        out["reopen_rate"] = _unavailable("reopen_count was not detected.")
    else:
        valid = pd.to_numeric(reopen, errors="coerce").dropna()
        out["reopen_rate"] = (_rate(valid.gt(0), total, "reopen_count") if len(valid)
                              else _unavailable("reopen_count has no valid values."))
        if len(valid):
            out["reopen_rate"]["coverage_pct"] = util.pct(len(valid), total)
    return out


def direction(metric: str) -> str:
    if metric in LOWER_IS_BETTER:
        return "lower"
    if metric in HIGHER_IS_BETTER:
        return "higher"
    raise ValueError(f"Metric has no outcome direction: {metric}")
