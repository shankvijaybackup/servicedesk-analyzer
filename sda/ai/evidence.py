"""Build an aggregate-only, allowlisted evidence packet for local AI."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_evidence_packet(analysis: dict[str, Any]) -> dict[str, Any]:
    """Return safe aggregate evidence without ticket text or identifiers.

    This is an explicit allowlist, rather than a recursive redactor. New fields
    in the core analysis cannot reach a model until they are reviewed here.
    """
    dq = analysis.get("data_quality", {})
    mttr = analysis.get("mttr", {})
    roi = analysis.get("opportunities", {}).get("roi_summary", {})

    themes = []
    for item in analysis.get("themes", []):
        themes.append(_pick(item, (
            "theme", "count", "pct", "mttr_median_hours", "mttr_p90_hours",
            "description_coverage_pct", "confidence",
        )))

    backlog = []
    for item in analysis.get("opportunities", {}).get("backlog", []):
        backlog.append(_pick(item, (
            "theme", "primary_type", "tickets_addressable",
            "est_deflectable_tickets_range", "risk_level", "confidence",
        )))

    return _json_safe({
        "data_quality": _pick(dq, (
            "total_records", "quality_score", "quality_grade", "fields_present",
            "fields_missing", "mttr_available",
        )),
        "mttr": {
            "available": bool(mttr.get("available", False)),
            "overall": _pick(mttr.get("overall", {}), (
            "n", "median_hours", "p90_hours",
            )),
        },
        "themes": themes[:5],
        "opportunities": {
            "roi_summary": _pick(roi, (
                "est_total_deflectable_range", "est_total_deflectable_pct_range",
            )),
            "backlog": backlog[:5],
        },
    })


def evidence_paths(packet: dict[str, Any]) -> set[str]:
    """Return leaf paths that an AI response may cite."""
    paths: set[str] = set()

    def walk(value: Any, path: str) -> None:
        if path:
            paths.add(path)
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}" if path else key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
        else:
            paths.add(path)

    walk(packet, "")
    return paths


def _pick(source: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: source[key] for key in keys if key in source}


def _json_safe(value: Any) -> Any:
    """Convert Pandas and NumPy scalars to JSON-compatible Python values."""
    if isinstance(value, dict):
        return {str(key): _json_safe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(child) for child in value]
    if value is pd.NA:
        return None
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value
