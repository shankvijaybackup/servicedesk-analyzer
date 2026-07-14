"""Step 1: Data Integrity First.

Inspect the dataset before any insight. Reports what exists, what is missing,
and how trustworthy the data is. It never invents a field: if something is
absent, it is reported as absent.
"""

from __future__ import annotations

import pandas as pd

from . import util
from .schema import col

# Canonical fields that materially affect the depth of analysis.
_KEY_FIELDS = [
    "ticket_id", "created", "resolved", "status", "priority", "type",
    "category", "subcategory", "assignment_group", "requester",
    "department", "application", "short_description",
]


def assess(df: pd.DataFrame, schema: dict) -> dict:
    total = int(len(df))
    mapping = schema["mapping"]

    # Duplicates: by ticket id if present, else by whole-row.
    id_col = mapping.get("ticket_id")
    if id_col:
        dup_count = int(df.duplicated(subset=[id_col]).sum())
        dup_basis = f"ticket id ({id_col})"
    else:
        dup_count = int(df.duplicated().sum())
        dup_basis = "entire row"

    # Date range from created.
    created = util.to_datetime(col(df, schema, "created"))
    date_range = None
    if created is not None and created.notna().sum() > 0:
        date_range = {
            "start": created.min().date().isoformat(),
            "end": created.max().date().isoformat(),
            "days": int((created.max() - created.min()).days),
            "parsed_share": util.pct(created.notna().sum(), total),
        }

    # MTTR availability.
    mttr = util.compute_mttr_hours(
        col(df, schema, "created"),
        col(df, schema, "resolved"),
        col(df, schema, "mttr_hours"),
    )
    mttr_available = mttr is not None and mttr.notna().sum() > 0
    mttr_source = None
    if mttr_available:
        mttr_source = ("explicit column" if mapping.get("mttr_hours")
                       else "derived from created/resolved timestamps")

    # Distinct value counts for key dimensions.
    def distinct(field: str):
        c = col(df, schema, field)
        return int(c.nunique(dropna=True)) if c is not None else None

    distinct_counts = {
        f: distinct(f) for f in
        ["type", "priority", "assignment_group", "category", "subcategory",
         "application", "department", "status"]
    }

    # Completeness (non-null share) for key fields present.
    completeness = {}
    for f in _KEY_FIELDS:
        c = col(df, schema, f)
        if c is not None:
            completeness[f] = util.pct(c.notna().sum(), total)

    score, grade, reasons = _quality(total, schema, date_range, mttr_available,
                                      completeness, dup_count)

    return {
        "total_records": total,
        "columns_in_file": list(df.columns),
        "fields_detected": schema["present"],
        "fields_missing": schema["missing"],
        "duplicate_records": dup_count,
        "duplicate_basis": dup_basis,
        "date_range": date_range,
        "mttr_available": mttr_available,
        "mttr_source": mttr_source,
        "distinct_counts": distinct_counts,
        "completeness_pct": completeness,
        "quality_score": score,
        "quality_grade": grade,
        "quality_reasons": reasons,
    }


def _quality(total, schema, date_range, mttr_available, completeness, dup_count):
    """A transparent 0-100 score. Every deduction is listed as a reason."""
    score = 100
    reasons: list[str] = []

    for field, penalty, label in [
        ("created", 12, "no reliable created date"),
        ("resolved", 10, "no resolved/closed date (MTTR limited)"),
        ("category", 8, "no category field"),
        ("priority", 6, "no priority field"),
        ("assignment_group", 6, "no assignment group"),
        ("application", 6, "no application/CI field"),
        ("short_description", 10, "no description/summary text to classify on"),
    ]:
        if field in schema["missing"]:
            score -= penalty
            reasons.append(f"-{penalty}: {label}")

    if not mttr_available:
        score -= 10
        reasons.append("-10: MTTR cannot be computed")

    if total < 200:
        score -= 8
        reasons.append(f"-8: small sample ({total} records) limits confidence")

    if dup_count:
        pen = min(10, 1 + dup_count * 20 // max(total, 1))
        score -= pen
        reasons.append(f"-{pen}: {dup_count} duplicate records")

    # Text completeness matters for classification quality.
    desc_complete = completeness.get("short_description")
    if desc_complete is not None and desc_complete < 80:
        score -= 6
        reasons.append(f"-6: description only {desc_complete}% populated")

    score = max(0, min(100, score))
    grade = ("Strong" if score >= 80 else "Adequate" if score >= 60
             else "Weak" if score >= 40 else "Poor")
    return score, grade, reasons
